# SCOOP

**SCOOP** is a framework that exploits all artifacts associated with the construction of an RDF graph, i.e. data schemas, ontologies, and mapping rules, and integrates the SHACL shapes extracted from each artifact into a unified shapes graph.

We implemented **SCOOP-All**, **SCOOP-Prior**, and **SCOOP-Prior-R**. 

We incorporate RML2SHACL, Astrea, and XSD2SHACL.

## Installation

## Command Line Use
For command line use:

To translate RML/Ontology/XSD to SHACL shapes and integrate the all shapes to one shape (the default priority is rml>ontology>xsd):

```
$ python main.py --mode [priority/priorityR/all] --parallel [True/False] --mappings [PATH_TO_RML/PATH_TO_RML_FOLDER] --ontology [PATH_TO_ONTOLOGY/PATH_TO_ONTOLOGY_FOLDER] --xsd [PATH_TO_XSD/PATH_TO_XSD_FOLDER] -xsd [PATH_TO_ADJUSTMENT_XSD/PATH_TO_ADJUSTMENT_RML_FOLDER] --priority PRIORITY1 PRIORITY2 PRIORITY3 -o OUT_PUT_PATH
```

For example:

```
$ python main.py --mode all --parallel True --mappings usecases/RINF/mappings/ --xsd usecases/RINF/schema/ -xr usecases/RINF/mappings/ --ontology usecases/RINF/ontology/ontology.ttl -o integrated_shapes_all_rml_owl_xsd.ttl 
```

Where
 - `--mode` is 
 - `--parallel` is 
 - `--mappings` is 
 - `--xsd` is 
 - `--ontology` is 
 - `-xr` is
 - `-o` is

Full CLI Usage options:
```

```