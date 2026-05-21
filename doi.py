import hashlib
import os
import tempfile
import xml.etree.ElementTree as ET

import requests
from fsspec import AbstractFileSystem, filesystem
from fsspec.registry import register_implementation

class DOIDictFileSystem(AbstractFileSystem):
    protocol = "doi"

    def __init__(self, doi=None, cache_dir=None, **kwargs):
        super().__init__(**kwargs)
        if doi is None:
            raise ValueError("Must provide a DOI")
        self.root_dir = self.fetch_namespace_from_doi(doi)
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "doi_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    @classmethod
    def fetch_namespace_from_doi(cls, doi):
        accept_str = "application/metalink4+xml"
        headers = {"Accept": accept_str}
        response = requests.get(
            f"https://doi.org/{doi}", headers=headers, allow_redirects=True
        )

        if accept_str not in response.headers.get("Content-Type", ""):
            raise ValueError("No Metalink available")

        root_xml = ET.fromstring(response.text)
        ns = {"ml": root_xml.tag.split("}")[0].strip("{")}
        urls = [url.text for url in root_xml.findall(".//ml:url", namespaces=ns)]
        filenames = [
            file_elem.attrib["name"]
            for file_elem in root_xml.findall(".//ml:file", namespaces=ns)
        ]

        root_dir = cls.new_dir()
        counter = 0
        for file in filenames:
            parts = file.strip("/").split("/")
            current_dir = root_dir
            for i, item in enumerate(parts):
                is_dir = i < len(parts) - 1
                if is_dir:
                    if not cls.dir_has_item(current_dir, item):
                        cls.create_dir(current_dir, item)
                    current_dir = cls.change_dir(current_dir, item)
                else:
                    cls.create_file(current_dir, item, urls[counter])
                    counter += 1

        return root_dir

    @staticmethod
    def create_file(dir, name, url):
        dir[name] = url

    @classmethod
    def create_dir(cls, dir, name):
        new_directory = cls.new_dir()
        dir[name] = new_directory
        return new_directory

    @staticmethod
    def dir_has_item(dir, name):
        return name in dir

    @staticmethod
    def new_dir():
        return {}

    @staticmethod
    def change_dir(dir, name):
        return dir[name]

    def _get_node(self, path):
        parts = path.strip("/").split("/") if path.strip("/") else []
        node = self.root_dir
        for part in parts:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                raise FileNotFoundError(path)
        return node

    def info(self, path):
        node = self._get_node(path)
        if isinstance(node, dict):
            return {"name": path, "type": "directory", "size": 0}
        else:
            resp = requests.head(node, allow_redirects=True)
            size = int(resp.headers.get("Content-Length", 0))
            return {"name": path, "type": "file", "size": size}

    def _cache_path(self, url):
        # Hash URL to create stable local filename
        h = hashlib.sha256(url.encode()).hexdigest()
        return os.path.join(self.cache_dir, h)

    def ls(self, path, detail=True):
        node = self._get_node(path)
        if not isinstance(node, dict):
            raise NotADirectoryError(path)

        items = []
        for name, value in node.items():
            full_path = f"{path.rstrip('/')}/{name}" if path else name
            if isinstance(value, dict):
                entry = {"name": full_path, "type": "directory", "size": 0}
            else:
                entry = {"name": full_path, "type": "file", "size": 0}
            items.append(entry)
        return items if detail else [x["name"] for x in items]

    def open(self, path, mode="rb", **kwargs):
        if "r" not in mode:
            raise NotImplementedError("This FS is read-only.")
        node = self._get_node(path)
        if isinstance(node, dict):
            raise IsADirectoryError(path)

        cache_file = self._cache_path(node)
        if not os.path.exists(cache_file):
            # Download and cache
            resp = requests.get(node, stream=True)
            resp.raise_for_status()
            with open(cache_file, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        return open(cache_file, mode)

    def clear_cache(self):
        """Delete all cached files."""
        for f in os.listdir(self.cache_dir):
            os.remove(os.path.join(self.cache_dir, f))

    def cache_size(self):
        """Return total size of cache in bytes."""
        return sum(
            os.path.getsize(os.path.join(self.cache_dir, f))
            for f in os.listdir(self.cache_dir)
        )

    def list_cache(self):
        """List cached files (hashes only)."""
        return os.listdir(self.cache_dir)

register_implementation("doi", DOIDictFileSystem)