import requests
import fsspec
from fsspec.spec import AbstractFileSystem
import xml.etree.ElementTree as ET

doi = "10.60717/041caef8-645a-4dd8-b12d-892ee03084c2"
headers = {"Accept": "application/metalink4+xml"}
response = requests.get(f"https://doi.org/{doi}", headers = headers, allow_redirects=True)

if "metalink" in response.headers.get("Content-Type", ""):
    root = ET.fromstring(response.text)
    ET.indent(root, space="  ", level=0)
    xml_string_pretty = ET.tostring(root, encoding="utf-8").decode("utf-8")

    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(xml_string_pretty)

    ns = {'ml':root.tag.split("}")[0].strip("{")}
    urls = [url.text for url in root.findall(".//ml:url", namespaces=ns)]
    filenames = [file_elem.attrib['name'] for file_elem in root.findall(".//ml:file", namespaces=ns)]
    
    names = []
    i = 0
    for filename in filenames:
        names.append(filename)

    url_dict = {name: None for name in names}

    i = 0
    for url in urls:
        url_dict[filenames[i]] = {'address': url}
        i += 1
       # with fsspec.open(url, mode='rb') as f:
        #    content = f.read()
         #   print(f"Downloaded {len(content)} bytes from {url}")

    for key in url_dict.keys():
        print(key)

else:
    print("No Metalink available")