import requests
import xml.etree.ElementTree as ET
import fsspec
import shlex
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
import os
import hashlib
import tempfile

def create_file(dir, name, url):
    dir[name] = url

def create_dir(dir, name):
    new_directory = new_dir()
    dir[name] = new_directory
    return new_directory

def dir_has_item(dir, name):
    return name in dir

def new_dir():
    return {}

def change_dir(dir, name):
    return dir[name]

def fetch_namespace_from_doi(doi):
    headers = {"Accept": "application/metalink4+xml"}
    response = requests.get(f"https://doi.org/{doi}", headers=headers, allow_redirects=True)
    
    if "application/metalink4+xml" not in response.headers.get("Content-Type", ""):
        raise ValueError("No Metalink available")

    root_xml = ET.fromstring(response.text)
    ns = {"ml": root_xml.tag.split("}")[0].strip("{")}
    urls = [url.text for url in root_xml.findall(".//ml:url", namespaces=ns)]
    filenames = [
        file_elem.attrib["name"]
        for file_elem in root_xml.findall(".//ml:file", namespaces=ns)
    ]

    root_dir = new_dir()
    counter = 0
    for file in filenames:
        parts = file.strip("/").split("/")
        current_dir = root_dir
        for i, item in enumerate(parts):
            is_dir = i < len(parts) - 1
            if is_dir:
                if not dir_has_item(current_dir, item):
                    create_dir(current_dir, item)
                current_dir = change_dir(current_dir, item)
            else:
                create_file(current_dir, item, urls[counter])
                counter += 1

    return root_dir

class DOIDictFileSystem(fsspec.AbstractFileSystem):
    protocol = "doi_dict"

    def __init__(self, root_dir, cache_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.root_dir = root_dir
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "doi_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

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

# Build the directory tree from DOI
DOI = input("Please enter the DOI: ")
root = fetch_namespace_from_doi(DOI)

# Create FS object
fs = DOIDictFileSystem(root)


from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
import os

class DOICompleter(Completer):
    def __init__(self, fs, cwd_ref):
        """
        fs: your DOIDictFileSystem
        cwd_ref: a reference (list or dict) holding the current working directory string
                 so we can update it dynamically in REPL
        """
        self.fs = fs
        self.cwd_ref = cwd_ref

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.strip()
        parts = text.split()
        if not parts:
            return

        cmd = parts[0]
        arg = parts[-1] if len(parts) > 1 else ""

        # Only complete on commands that expect paths
        if cmd in ("ls", "cd", "cat", "head", "info", "get"):
            cwd = self.cwd_ref[0]  # current working directory
            base_dir = cwd

            if "/" in arg:
                base_dir, prefix = arg.rsplit("/", 1)
                base_dir = base_dir.strip("/")
            else:
                prefix = arg

            try:
                items = self.fs.ls(base_dir)
            except Exception:
                return

            for item in items:
                name = item["name"].split("/")[-1]
                if name.startswith(prefix):
                    yield Completion(name, start_position=-len(prefix))


def doi_shell(fs):
    cwd = [""]
    session = PromptSession(completer=DOICompleter(fs, cwd))

    while True:
        try:
            cmdline = session.prompt(f"doi:/{cwd[0] or ''}$ ")
            parts = cmdline.strip().split()
            if not parts:
                continue
            cmd, *args = parts

            if cmd in ("exit", "quit"):
                break

            elif cmd == "pwd":
                print("/" + cwd[0] if cwd[0] else "/")

            elif cmd == "ls":
                path = args[0] if args else cwd[0]
                try:
                    items = fs.ls(path)
                    for item in items:
                        name = item["name"].split("/")[-1]
                        if item["type"] == "directory":
                            text = FormattedText([("ansiblue", name)])   # blue for dirs
                        else:
                            text = FormattedText([("ansigreen", name)])  # green for files
                        print_formatted_text(text)
                except Exception as e:
                    print("Error:", e)

            elif cmd == "cd":
                if not args:
                    cwd[0] = ""
                else:
                    new_path = args[0] if args[0].startswith("/") else f"{cwd[0]}/{args[0]}".strip("/")
                    try:
                        info = fs.info(new_path)
                        if info["type"] == "directory":
                            cwd[0] = new_path
                        else:
                            print("Not a directory:", new_path)
                    except Exception as e:
                        print("Error:", e)

            elif cmd == "cat":
                if not args:
                    print("Usage: cat <filename>")
                else:
                    path = args[0] if args[0].startswith("/") else f"{cwd[0]}/{args[0]}".strip("/")
                    try:
                        with fs.open(path, "rb") as f:
                            print(f.read().decode(errors="replace"))
                    except Exception as e:
                        print("Error:", e)

            elif cmd == "head":
                if not args or info["type"] == "directory":
                    print("Usage: head <filename>")
                else:
                    path = args[0] if args[0].startswith("/") else f"{cwd[0]}/{args[0]}".strip("/")
                    try:
                        with fs.open(path, "rb") as f:
                            print(f.read(500).decode(errors="replace"))
                    except Exception as e:
                        print("Error:", e)

            elif cmd == "info":
                if not args:
                    print("Usage: info <path>")
                else:
                    path = args[0] if args[0].startswith("/") else f"{cwd[0]}/{args[0]}".strip("/")
                    try:
                        info = fs.info(path)
                        print(f"Path: {path}")
                        print(f"Type: {info['type']}")
                        print(f"Size: {info['size']} bytes")
                    except Exception as e:
                        print("Error:", e)

            elif cmd == "get":
                if not args:
                    print("Usage: get <remote-path> [local-path]")
                else:
                    remote_path = args[0] if args[0].startswith("/") else f"{cwd[0]}/{args[0]}".strip("/")
                    local_path = args[1] if len(args) > 1 else os.path.basename(remote_path)
                    try:
                        with fs.open(remote_path, "rb") as fsrc, open(local_path, "wb") as fdst:
                            fdst.write(fsrc.read())
                        print(f"Downloaded {remote_path} → {local_path}")
                    except Exception as e:
                        print("Error:", e)

            elif cmd == "cache":
                if not args:
                    print("Usage: cache <info|list|clear>")
                else:
                    subcmd = args[0]
                    if subcmd == "info":
                        print(f"Cache dir: {fs.cache_dir}")
                        print(f"Cache size: {fs.cache_size()} bytes")
                    elif subcmd == "list":
                        print("Cached files:")
                        for f in fs.list_cache():
                            print(" ", f)
                    elif subcmd == "clear":
                        fs.clear_cache()
                        print("Cache cleared")
                    else:
                        print("Unknown cache subcommand")

            else:
                print("Commands: ls, cd, pwd, cat, head, info, get, cache, exit")

        except (KeyboardInterrupt, EOFError):
            print()
            break


doi_shell(fs)