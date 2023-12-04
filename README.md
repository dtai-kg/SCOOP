# SCOOP

**SCOOP** is a framework that exploits all artifacts associated with the construction of an RDF graph, i.e. data schemas, ontologies, and mapping rules, and integrates the SHACL shapes extracted from each artifact into a unified shapes graph.

We implemented **SCOOP-All**, **SCOOP-Prior**, and **SCOOP-Prior-R**. 

We incorporate [RML2SHACL](https://github.com/RMLio/RML2SHACL), [Astrea](https://github.com/oeg-upm/astrea), and [XSD2SHACL](https://github.com/dtai-kg/XSD2SHACL).

## Installation
Using git clone:

```
$ git clone https://github.com/dtai-kg/SCOOP.git
```

Installing reqruiements:

```
$ pip install -r requirements
```

## Command Line Use
For command line use:

```
$ python main.py --mode priority/priorityR/all --priority source1 source2 source3 --parallel true/false -m PATH_TO_RML/PATH_TO_RML_FOLDER -o PATH_TO_ONTOLOGY/PATH_TO_ONTOLOGY_FOLDER 
-x PATH_TO_XSD/PATH_TO_XSD_FOLDER -xr PATH_TO_ADJUSTMENT_XSD/PATH_TO_ADJUSTMENT_RML_FOLDER 
-ot OUT_PUT_PATH
```

For example:

```
$ python main.py --mode all --parallel True -m usecases/RINF/mappings/ -o usecases/RINF/ontology/ontology.ttl -x usecases/RINF/schema/ -xr usecases/RINF/mappings/
-ot SCOOP_all_rml_owl_xsd.ttl 
```

Where:
 - `--mode` is used to specify the integration mode, with three available options: "priority", "priorityR", and "all". Use this option to control the behavior of integration.
 - `--priority` is used to specify the priority order of sources, default is mapping rules higher than ontologies higher than XSD.
 - `--parallel` is used to specify whether parallel mode is enabled. If set to `True`, parallel processing may be used during integration for improved efficiency; if set to `False`, parallel processing is not utilized.
 - `-m`, `--mappings` is used to specify the path to the folder or mapping files to be translated. Multiple file paths can be provided.
 - `-x`, `--xsd` is used to specify the path to the folder or XSD files to be translated. Multiple file paths can be provided.
 - `-o`, `--ontology` is used to specify the path to the folder or ontology files to be translated. Multiple file paths can be provided.
 - `-xr`, `--xsd_rml` is used to specify the RML file or folder path for post-adjustment of XSD-driven shapes. Multiple file paths can be provided.
 - `-ot`, `--output` is used to specify the output file path and name. The default value is "shape_integration.ttl". If not provided, the result will be saved to the default file.


Full CLI Usage options:
```
$ python main.py -h
usage: main.py [-h] [--mode] [--parallel] [--priority] [-m --mappings] [-o --ontology]
               [-x --xsd] [-xr --xsd_rml] [-ot --output]

optional arguments:
  -h, --help            show this help message and exit
  --mode                integration mode: priority, priorityR, or all (default: priority)
  --parallel            parallel mode: True or False (default: False)
  --priority            [PRIORITY ...]
                        List of priority for integrating shapes from diverse sources (default: ['rml', 'ontology', 'xsd'])
  -m --mappings         [MAPPINGS ...]
                        Path to folder or mapping files to be translated
  -o --ontology         [ONTOLOGY ...]
                        Path to folder or ontology files to be translated
  -x --xsd              [XSD ...]   Path to folder or xsd file to be translated
  -xr --xsd_rml         [XSD_RML ...]
                        Path to folder or rml file for post-adjustment of XSD-driven shape
  -ot --output          Output file (default: shape_integration.ttl)
```