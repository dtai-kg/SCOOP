# SCOOP

**SCOOP** is a framework that exploits all artifacts associated with the construction of an RDF graph, i.e. data schemas, ontologies, and mapping rules, and integrates the SHACL shapes extracted from each artifact into a unified shapes graph.

We implemented **SCOOP-All**, **SCOOP-Prior**, and **SCOOP-Prior-R**. 

We incorporate [RML2SHACL](https://github.com/RMLio/RML2SHACL), [Astrea](https://github.com/oeg-upm/astrea), and [XSD2SHACL](https://github.com/dtai-kg/XSD2SHACL).

## Installation

## Command Line Use
For command line use:

```
$ python main.py --mode [priority/priorityR/all] --parallel [True/False] --mappings [PATH_TO_RML/PATH_TO_RML_FOLDER] --ontology [PATH_TO_ONTOLOGY/PATH_TO_ONTOLOGY_FOLDER] --xsd [PATH_TO_XSD/PATH_TO_XSD_FOLDER] -xsd [PATH_TO_ADJUSTMENT_XSD/PATH_TO_ADJUSTMENT_RML_FOLDER] --priority PRIORITY1 PRIORITY2 PRIORITY3 -o OUT_PUT_PATH
```

For example:

```
$ python main.py --mode all --parallel True --mappings usecases/RINF/mappings/ --xsd usecases/RINF/schema/ -xr usecases/RINF/mappings/ --ontology usecases/RINF/ontology/ontology.ttl -o integrated_shapes_all_rml_owl_xsd.ttl 
```

Where:
 - `--mode` is used to specify the integration mode, with three available options: "priority", "priorityR", and "all". Use this option to control the behavior of integration.
 - `--parallel` is used to specify whether parallel mode is enabled. If set to `True`, parallel processing may be used during integration for improved efficiency; if set to `False`, parallel processing is not utilized.
 - `--mappings` is used to specify the path to the folder or mapping files to be translated. Multiple file paths can be provided.
 - `--xsd` is used to specify the path to the folder or XSD files to be translated. Multiple file paths can be provided.
 - `--ontology` is used to specify the path to the folder or ontology files to be translated. Multiple file paths can be provided.
 - `-xr` is used to specify the RML file or folder path for post-adjustment of XSD-driven shapes. Multiple file paths can be provided.
 - `-o` is used to specify the output file path and name. The default value is "shape_integration.ttl". If not provided, the result will be saved to the default file.


Full CLI Usage options:
```
$ python main.py -h
usage: main.py [-h] [--mode MODE] [--parallel PARALLEL] [--priority PRIORITY [PRIORITY ...]]
               [--mappings MAPPINGS [MAPPINGS ...]] [--ontology ONTOLOGY [ONTOLOGY ...]]
               [--xsd XSD [XSD ...]] [--xsd_rml XSD_RML [XSD_RML ...]] [--output OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --mode MODE           integration mode: priority, priorityR, or all (default: priority)
  --parallel PARALLEL   parallel mode: True or False (default: False)
  --priority PRIORITY [PRIORITY ...]
                        List of priority for integrating shapes from diverse sources (default: ['rml', 'ontology', 'xsd'])
  --mappings MAPPINGS [MAPPINGS ...]
                        Path to folder or mapping files to be translated
  --ontology ONTOLOGY [ONTOLOGY ...]
                        Path to folder or ontology files to be translated
  --xsd XSD [XSD ...]   Path to folder or xsd file to be translated
  --xsd_rml XSD_RML [XSD_RML ...]
                        Path to folder or rml file for post-adjustment of XSD-driven shape
  --output OUTPUT, -o OUTPUT
                        Output file (default: shape_integration.ttl)
```