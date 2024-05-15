import json
from rdflib import Graph, Namespace, Literal, URIRef, RDF, BNode
from .utils import json_load

SHACL = Namespace("http://www.w3.org/ns/shacl#")
predefined_datatype = json_load("src/vocabulary/xmlschema11_2.json")


def transConstraints(g,sub,k,v,logger):
    base = None
    if k == "name":
        g.add((sub, SHACL["name"], Literal(v)))
    elif k == "datatype":
        if isinstance(v, str):
            g.add((sub, SHACL["datatype"], transDatatype(v)))
        else:
            if v.get("base"):
                base = transDatatype(v.get("base"))
                g.add((sub, SHACL["datatype"], base))
            if checkInconsistency(base,v,logger) == False:
                # Discard the constraint if it is inconsistent
                return g
            if v.get("minimum"):
                try:
                    g.add((sub, SHACL["minInclusive"], Literal(int(v.get("minimum")))))
                except:
                    g.add((sub, SHACL["minInclusive"], Literal(v.get("minimum"))))
            if v.get("maximum"):
                try:
                    g.add((sub, SHACL["maxInclusive"], Literal(int(v.get("maximum")))))
                except:
                    g.add((sub, SHACL["maxInclusive"], Literal(v.get("maximum"))))
            if v.get("minInclusive"):
                try:
                    g.add((sub, SHACL["minInclusive"], Literal(int(v.get("minInclusive")))))
                except:
                    g.add((sub, SHACL["minInclusive"], Literal(v.get("minInclusive"))))
            if v.get("maxInclusive"):
                try:
                    g.add((sub, SHACL["maxInclusive"], Literal(int(v.get("maxInclusive")))))
                except:
                    g.add((sub, SHACL["maxInclusive"], Literal(v.get("maxInclusive"))))
            if v.get("minExclusive"):
                try:
                    g.add((sub, SHACL["minExclusive"], Literal(int(v.get("minExclusive")))))
                except:
                    g.add((sub, SHACL["minExclusive"], Literal(v.get("minExclusive"))))
            if v.get("maxExclusive"):
                try:
                    g.add((sub, SHACL["maxExclusive"], Literal(int(v.get("maxExclusive")))))
                except:
                    g.add((sub, SHACL["maxExclusive"], Literal(v.get("maxExclusive"))))
            if v.get("length"):
                g.add((sub, SHACL["maxLength"], Literal(int(v.get("length")))))
                g.add((sub, SHACL["minLength"], Literal(int(v.get("length")))))
            if v.get("minLength"):
                g.add((sub, SHACL["minLength"], Literal(int(v.get("minLength")))))
            if v.get("maxLength"):
                g.add((sub, SHACL["maxLength"], Literal(int(v.get("maxLength")))))
            # if v.get("format"):
            # TODO Check format translation
            #     g.add((sub, SHACL["pattern"], Literal(v.get("format"))))
    elif k == "required":
        if v == True:
            g.add((sub, SHACL["minCount"], Literal(1)))
    elif k == "default":
        g.add((sub, SHACL["defaultValue"], Literal(v)))
    elif k == "lang":
        bn = BNode()
        g.add((sub, SHACL["languageIn"], bn))
        g.add((bn, RDF.first, Literal(v)))
        g.add((bn, RDF.rest, RDF.nil))

    return g

def transDatatype(datatype):
    #translate from complete built-in datatypes, based on [xmlschema11-2]
    if datatype in predefined_datatype:
        return URIRef(predefined_datatype[datatype])
    else:
        raise ValueError(f"Datatype '{datatype}' not found in default datatypes.")


def addDefaultConstriants(g, virtualShapes):
    # Add default datatype string to each property shape who doesn't have datatype
    for s,p,o in g.triples((None, SHACL["path"], None)):
        if (s not in virtualShapes) and (not (s, SHACL["datatype"], None) in g):
            g.add((s, SHACL["datatype"], URIRef(predefined_datatype["string"])))

    return g

def checkInconsistency(base,v,logger):
    if (v.get("length") or v.get("minLength") or v.get("maxLength")) and base and (base != URIRef(predefined_datatype["string"]) or base != URIRef(predefined_datatype["normalizedString"]) or base != URIRef(predefined_datatype["token"]) or base != URIRef(predefined_datatype["xml"]) or base != URIRef(predefined_datatype["html"]) or base != URIRef(predefined_datatype["json"])):
        logger.error("Length constraints are only allowed for string or its subtype")
        return False
    if (v.get("minimum") or v.get("maximum") or v.get("minInclusive") or v.get("maxInclusive") or v.get("minExclusive") or v.get("maxExclusive")) and base and base == URIRef(predefined_datatype["string"]):
        logger.error("Numeric constraints are not allowed for string datatypes")
        return False
    if v.get("minimum") and v.get("maximum") and v.get("minimum") > v.get("maximum"):
        logger.error("Minimum value is greater than maximum value")
        return False
    if v.get("minInclusive") and v.get("maxInclusive") and v.get("minInclusive") > v.get("maxInclusive"):
        logger.error("Minimum inclusive value is greater than maximum inclusive value")
        return False
    if v.get("minExclusive") and v.get("maxExclusive") and v.get("minExclusive") > v.get("maxExclusive"):
        logger.error("Minimum exclusive value is greater than maximum exclusive value")
        return False
    if v.get("minInclusive") and v.get("maxExclusive") and v.get("minInclusive") >= v.get("maxExclusive"):
        logger.error("Minimum inclusive value is greater than or equal to maximum exclusive value")
        return False
    if v.get("minExclusive") and v.get("maxInclusive") and v.get("minExclusive") >= v.get("maxInclusive"):
        logger.error("Minimum exclusive value is greater than or equal to maximum inclusive value")
        return False
    if v.get("minInclusive") and v.get("minExclusive"):
        logger.error("Both minimum inclusive and minimum exclusive values are defined")
        return False
    if v.get("maxInclusive") and v.get("maxExclusive"):
        logger.error("Both maximum inclusive and maximum exclusive values are defined")
        return False
    if v.get("minLength") and v.get("maxLength") and v.get("minLength") > v.get("maxLength"):
        logger.error("Minimum length is greater than maximum length")
        return False
    if v.get("length") and v.get("minLength") and v.get("length") < v.get("minLength"):
        logger.error("Length is less than minimum length")
        return False
    if v.get("length") and v.get("maxLength") and v.get("length") > v.get("maxLength"):
        logger.error("Length is greater than maximum length")
        return False
    if v.get("minLength") and v.get("maxLength") and v.get("minLength") > v.get("maxLength"):
        logger.error("Minimum length is greater than maximum length")
        return False
    # if v.get("minCount") and v.get("maxCount") and v.get("minCount") > v.get("maxCount"):
    #     logger.error("Minimum count is greater than maximum count")
    # if v.get("minCount") and v.get("maxCount") and v.get("minCount") == v.get("maxCount"):
    #     logger.error("Minimum count is equal to maximum count")
    # if v.get("minCount") and v.get("maxCount") and v.get("minCount") > v.get("maxCount"):
    #     logger.error("Minimum count is greater than maximum count")
    return True