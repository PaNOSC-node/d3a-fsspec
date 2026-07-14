The program's purpose is to access datasets based on a given DOI via Metalink parsing. It works as follows:

When running, the program will ask to input a DOI

```
Please enter the DOI: https://doi.org/10.60717%2F39cc1229-6933-4d15-a4a8-aff45d7673c4
doi:/$
```

User then has several options:

- `ls` for listing files and directories
- `cd` for changing to a different directory
- `pwd` for checking what the current directory is
- `cat` for printing the whole file
- `head` for printing the first 500 bytes of a file
- `info` for the size and path of the file
- `get` for downloading the file into a temp folder
- `cache info` for the size and path of cached files
- `cache list` for list of files in hash format
- `cache clear` for clearing the cache

Example workflow:
```
Please enter the DOI: https://doi.org/10.60717%2F041caef8-645a-4dd8-b12d-892ee03084c2
doi:/$ ls
ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-3532648465850078741
ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-347262956019794909
ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-8070603949527830319
ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-434226345705388838
doi:/$ cd ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-3532648465850078741
doi:/ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-3532648465850078741$ pwd
/ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-3532648465850078741
doi:/ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-3532648465850078741$ cat reflectivity.ort
# # ORSO reflectivity data file | 1.1 standard | YAML encoding | https://www.reflectometry.org/
# # Grazing incidence off‐specular diffuse scattering measurement from liquid surfaces at fixed incident angle: a new method to extract specular reflectivity | 2024-02-29 | water | R(Qz)
...
doi:/ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-3532648465850078741$ head scicat_metadata.json
{
    "owner": "Chen Shen",
    "contactEmail": "chen.shen@desy.de",
...
doi:/ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-3532648465850078741$ info scicat_odb.json
Path: ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-3532648465850078741/scicat_odb.json
Type: file
Size: 445 bytes
doi:/ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-3532648465850078741$ get reflectivity.ort
Downloaded ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-3532648465850078741/reflectivity.ort → reflectivity.ort
doi:/ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-3532648465850078741$ cache info
Cache dir: C:\Users\akhund\AppData\Local\Temp\doi_cache
Cache size: 10854 bytes
doi:/ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-3532648465850078741$ cache list
Cached files:
  3dc63d233776f766d86b75549fc49902adf2310ea85911715144a7c88cd8fde4
  7bad3ee2e111b28d27b92045dc4e7ba356c06241240d16b378161f071729b7dd
doi:/ChenShen-Grazingincidenceoffspeculardiffusescatteringmeasurementfromliquidsurfacesatfixedincidentangleanewmethodtoextractspecularreflectivity-3532648465850078741$ cache clear
Cache cleared
```

## Installation

The `d3a-cli` program can be installed as a
[standalone command line tool](https://packaging.python.org/en/latest/guides/installing-stand-alone-command-line-tools/)
using, for example, `pipx` or `uv`

```shell
# install
pipx install git+https://github.com/PaNOSC-node/d3a-fsspec.git
# run
d3a-cli
```

For development, install it into a virtual environment in editable mode:

```shell
python -m venv venv
source venv/bin/activate
python -m pip install -e .
```
