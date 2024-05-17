import rdflib
import subprocess
import os
import requests


def translateFromUrl(ontology, output_file="output.ttl"):

    print("Start translating ontology url to SHACL shape by REST API", ontology)

    onto = {"ontologies": [ontology]}
    astrea_url = 'https://astrea.linkeddata.es/api/shacl/url'
    shacl_shape = requests.post(astrea_url, json = onto)

    graph = rdflib.Graph().parse(data=shacl_shape.text, format="turtle")
    graph = correctSHACL(graph)
    graph.serialize(destination=output_file, format='turtle')

    print("Saved SHACL shape to ", output_file)

def translateFromFile(ontology, output_file="output.ttl"):

    print("Start translating ontology file to SHACL shape by REST API", ontology)

    onto = {
    "ontology": rdflib.Graph().parse(ontology, format="turtle").serialize(format='turtle'),
    "serialisation": "TURTLE"
    }
    astrea_url = 'https://astrea.linkeddata.es/api/shacl/document'
    shacl_shape = requests.post(astrea_url, json = onto)
    graph = rdflib.Graph().parse(data=shacl_shape.text, format="turtle")
    graph = correctSHACL(graph)
    graph.serialize(destination=output_file, format='turtle')
    print("Saved SHACL shape to ", output_file)

def translateByJar(ontology, output_file="output.ttl"):

    print("Start translating ontology to SHACL shape by JAR", ontology)

    AstreaKG = f"{os.path.dirname(os.path.dirname(__file__))}/shape_generator/owl2shacl/src/Astrea-KG.ttl"
    astreajarpath = f"{os.path.dirname(os.path.dirname(__file__))}/shape_generator/owl2shacl/src/Astrea2SHACL.jar"
    ontology = f"{os.path.dirname(os.path.dirname(__file__))}/shape_generator/{ontology}"

    subprocesscommand = ['java', '-jar', astreajarpath, AstreaKG, ontology]
    result = subprocess.check_output(subprocesscommand, stderr=subprocess.STDOUT, text=True)
    graphs = result.split('Astrea2SHACLGraphDelimiter\n')
    for item in graphs:
        if item != "":
            graph = rdflib.Graph()
            graph.parse(data=item, format="turtle")
            graph = correctSHACL(graph)
            graph.serialize(destination=output_file, format='turtle')

    print("Saved SHACL shape to ", output_file)

def correctSHACL(shape):
    print("Start fixing OOWL-driven SHACL shapes")
    shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')
    checkList = [shaclNS.nodeKind, shaclNS.datatype, shaclNS.minCount, shaclNS.maxCount, shaclNS.minExclusive, shaclNS.maxExclusive, shaclNS.minInclusive, shaclNS.maxInclusive, shaclNS.minLength, shaclNS.maxLength, shaclNS.pattern, shaclNS.flags, shaclNS.languageIn, shaclNS.uniqueLang, shaclNS.qualifiedMinCount, shaclNS.qualifiedMaxCount]
    checkLiteralList = [shaclNS.minCount, shaclNS.maxCount, shaclNS.minExclusive, shaclNS.maxExclusive, shaclNS.minInclusive, shaclNS.maxInclusive, shaclNS.minLength, shaclNS.maxLength, shaclNS.qualifiedMinCount, shaclNS.qualifiedMaxCount]

    identifiers = []
    for s in shape.subjects(rdflib.RDF.type,shaclNS.NodeShape):
        identifiers.append(s)
    for s in shape.subjects(rdflib.RDF.type,shaclNS.PropertyShape):
        identifiers.append(s)
    
    for identifier in identifiers:
        for check in checkList:
            number_value = shape.value(identifier, check)

    for constraint in checkList:
        for s in identifiers:
            temp = []
            for value in shape.objects(s,constraint):
                if (constraint in checkLiteralList):
                    shape.remove((s,constraint,value))
                    value = rdflib.Literal(int(value))
                    shape.add((s,constraint,value))
                temp.append(value)
            if len(temp) > 1:
                for value in temp:
                    shape.remove((s,constraint,value))
    
    for s, p, o in shape.triples((None, None, shaclNS.PropertyShape)):
        path = shape.value(s, shaclNS.path)
        if not path:
            shape.remove((s, None, shaclNS.PropertyShape))
            # for s2, p2, o2 in shape.triples((s, None, None)):
            #     shape.remove((s2, p2, o2))
            # for s2, p2, o2 in shape.triples((None, None, s)):
            #     shape.remove((s2, p2, o2))
    return shape