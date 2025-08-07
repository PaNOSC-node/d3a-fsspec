import requests
import fsspec
from fsspec.spec import AbstractFileSystem
import xml.etree.ElementTree as ET

doi = "10.60717/041caef8-645a-4dd8-b12d-892ee03084c2"
headers = {"Accept": "application/metalink4+xml"}
response = requests.get(f"https://doi.org/{doi}", headers = headers, allow_redirects=True)

if "application/metalink4+xml" in response.headers.get("Content-Type", ""):
    root = ET.fromstring(response.text)
    ET.indent(root, space="  ", level=0)
    xml_string_pretty = ET.tostring(root, encoding="utf-8").decode("utf-8")

    ns = {'ml':root.tag.split("}")[0].strip("{")}
    urls = [url.text for url in root.findall(".//ml:url", namespaces=ns)]
    filenames = [file_elem.attrib['name'] for file_elem in root.findall(".//ml:file", namespaces=ns)]
    

    directory = {}
    i = 0
    for file in filenames:
        before_slash = ""
        for j, char in enumerate(filenames[i]):
            if char == "/":
                directory[before_slash] = {}
                before_slash = ""
            before_slash += char
            
            if j == len(filenames[i]) - 1:
                for x in range(j, -1, -1):
                    if filenames[i][j] == '/':
                        break
                    collected += filenames[i][j]
              


        
        i += 1
    
    print(directory)

else:
    print("No Metalink available")