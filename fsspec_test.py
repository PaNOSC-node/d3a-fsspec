import requests
import xml.etree.ElementTree as ET
import fsspec
import shlex
import io

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

    def __init__(self, root_dir, **kwargs):
        super().__init__(**kwargs)
        self.root_dir = root_dir  # nested dict from fetch_namespace_from_doi

    def _get_node(self, path):
        """Navigate through the nested dict to get the node for a path."""
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
        # node is a URL → fetch content
        resp = requests.get(node)
        resp.raise_for_status()
        return io.BytesIO(resp.content)

# Build the directory tree from DOI
root = fetch_namespace_from_doi("10.60717/041caef8-645a-4dd8-b12d-892ee03084c2")

# Create FS object
fs = DOIDictFileSystem(root)


def doi_shell(fs):
    cwd = ""  # current working directory

    while True:
        try:
            cmdline = input(f"doi:{cwd or '/'}$ ")
            parts = shlex.split(cmdline)  # handles quoted filenames
            if not parts:
                continue
            cmd, *args = parts

            if cmd == "exit" or cmd == "quit":
                break

            elif cmd == "ls":
                path = args[0] if args else cwd
                try:
                    items = fs.ls(path)
                    for item in items:
                        info = fs.info(item["name"])
                        print(item["name"].split("/")[-1], " -  size:", info["size"], "bytes")
                except Exception as e:
                    print("Error:", e)

            elif cmd == "cd":
                if not args:
                    cwd = ""
                else:
                    new_path = args[0] if args[0].startswith("/") else f"{cwd}/{args[0]}".strip("/")
                    try:
                        info = fs.info(new_path)
                        if info["type"] != "directory":
                            print("Not a directory:", new_path)
                        else:
                            cwd = new_path
                    except Exception as e:
                        print("Error:", e)

            elif cmd == "pwd":
                print("/" + cwd if cwd else "/")

            elif cmd == "cat":
                if not args:
                    print("Usage: cat <filename>")
                else:
                    path = args[0] if args[0].startswith("/") else f"{cwd}/{args[0]}".strip("/")
                    try:
                        with fs.open(path, "rb") as f:
                            print(f.read().decode(errors="replace"))
                    except Exception as e:
                        print("Error:", e)
            
            elif cmd == "info":
                if not args:
                    print("Usage: info <path>")
                else:
                    path = args[0] if args[0].startswith("/") else f"{cwd}/{args[0]}".strip("/")
                    try:
                        info = fs.info(path)
                        print(f"Path: {path}")
                        print(f"Type: {info['type']}")
                        print(f"Size: {info['size']} bytes")
                    except Exception as e:
                        print("Error:", e)

            elif cmd == "head":
                if not args:
                    print("Usage: head <filename>")
                else:
                    path = args[0] if args[0].startswith("/") else f"{cwd}/{args[0]}".strip("/")
                    try:
                        with fs.open(path, "rb") as f:
                            print(f.read(500).decode(errors="replace"))  # first 500 bytes
                    except Exception as e:
                        print("Error:", e)

            else:
                print("Commands: ls, cd, pwd, cat, head, info, exit")

        except (KeyboardInterrupt, EOFError):
            print()
            break


doi_shell(fs)