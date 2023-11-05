# Shapes-Integration
Integrating SHACL shapes derived from diverse source (e.g., RML, OWL, XSD, CSVW, Json Schema)

## Usage

To translate RML/Ontology/XSD to SHACL shapes and integrate the all shapes to one shape (the default priority is rml>ontology>xsd):

```
$ python main.py -r PATH_TO_RML/PATH_TO_RML_FOLDER -o PATH_TO_ONTOLOGY/PATH_TO_ONTOLOGY_FOLDER -x PATH_TO_XSD/PATH_TO_XSD_FOLDER -p PRIORITY1 PRIORITY2 PRIORITY3 -o OUT_PUT_PATH
```

For example:

```
$ python main.py -r usecases/RINF/mappings/ -x usecases/RINF/schema/
```

## Conflict Checking 
The added constraints can not cause the original shape to become unsatisfiable

Confirmed constraint list: 

- [X] class
- [X] nodeKind
- [X] datatype
- [X] minCount 
- [X] maxCount
- [X] minExclusive
- [X] maxExclusive
- [X] minInclusive
- [X] maxInclusive
- [X] minLength
- [X] maxLength
- [X] pattern
- [X] flags
- [X] languageIn
- [X] uniqueLang
- [X] equals
- [X] disjoint
- [X] lessThan
- [X] lessThanOrEquals 
- [X] not
- [X] and 
- [X] or
- [X] xone
- [X] node 
- [X] hasValue
- [X] in

## OWL2SHACL

- [ ] nodeKind 
- [ ] or
- [ ] minCount
- [ ] axCount