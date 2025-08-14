import requests
import fsspec
from fsspec.spec import AbstractFileSystem
import xml.etree.ElementTree as ET

doi = "10.60717/041caef8-645a-4dd8-b12d-892ee03084c2"
headers = {"Accept": "application/metalink4+xml"}
response = requests.get(f"https://doi.org/{doi}", headers = headers, allow_redirects=True)

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


if "application/metalink4+xml" in response.headers.get("Content-Type", ""):
    root = ET.fromstring(response.text)
    ET.indent(root, space="  ", level=0)
    xml_string_pretty = ET.tostring(root, encoding="utf-8").decode("utf-8")

    ns = {'ml':root.tag.split("}")[0].strip("{")}
    urls = [url.text for url in root.findall(".//ml:url", namespaces=ns)]
    filenames = [file_elem.attrib['name'] for file_elem in root.findall(".//ml:file", namespaces=ns)]
    

    root = new_dir()
    counter = 0
    for file in filenames:
        pe = file.strip("/").split("/")
        current_dir = root
        
        for i, item in enumerate(pe):
            is_dir = i < len(pe)-1
            if is_dir:
                if not dir_has_item(current_dir, item):
                    create_dir(current_dir, item)
                current_dir = change_dir(current_dir, item)

            else:
                create_file(current_dir, item, urls[counter])
                counter += 1
    
    print(root)
   

else:
    print("No Metalink available")