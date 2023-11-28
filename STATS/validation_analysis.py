from pyshacl import validate
import rdflib
from rdflib import Graph, Namespace
import os
import sys


f = open("STATS/validation/validation.txt", "w")
shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')

# Load the shacl graph
for validation_file in os.listdir("STATS/validation/"):
    validation_result = {}
    all_error = set()
    if validation_file.endswith("validation.ttl"):
        print("Analyzing", validation_file)
        f.write("=========="+validation_file+"\n")
        g = rdflib.Graph().parse("STATS/validation/"+validation_file, format="ttl")
        for s, p, o in g.triples((None, shaclNS.sourceConstraintComponent, None)):
            node = g.value(s, shaclNS.focusNode)
            path = g.value(s, shaclNS.resultPath)
            value = g.value(s, shaclNS.value)
            l = validation_result.get(o,set())
            l.add((node, path, value))
            validation_result[o] = l
            if o != shaclNS.MinCountConstraintComponent and o!= shaclNS.MaxCountConstraintComponent:
                all_error.add((node, path, value))
            
        for key, value in validation_result.items():
            f.write(str(key) + " " + str(len(value)) + "\n")
        f.write("All errors: " + str(len(all_error)) + "\n")
 

for validation_file in os.listdir("STATS/validation/temp"):
    if validation_file.endswith("validation.ttl"):
        print("Analyzing", validation_file)
        f.write("=========="+validation_file+"\n")
        g = rdflib.Graph().parse("STATS/validation/temp/"+validation_file, format="ttl")
        for s, p, o in g.triples((None, shaclNS.sourceConstraintComponent, None)):
            node = g.value(s, shaclNS.focusNode)
            path = g.value(s, shaclNS.resultPath)
            value = g.value(s, shaclNS.value)
            l = validation_result.get(o,set())
            l.add((node, path, value))
            validation_result[o] = l
            if o != shaclNS.MinCountConstraintComponent and o!= shaclNS.MaxCountConstraintComponent:
                all_error.add((node, path, value))
            
        for key, value in validation_result.items():
            f.write(str(key) + " " + str(len(value)) + "\n")
        f.write("All errors: " + str(len(all_error)) + "\n")
        



# validation_shape_graph = Graph().parse("shacl-shacl.ttl", format="turtle")
# #sg = rdflib.Graph().parse("STATS/all_countries_combined_QSE_0.1_100_SHACL.ttl", format="ttl")
# r = validate(sg, shacl_graph=validation_shape_graph, ont_graph=None,
#                 inference='rdfs', abort_on_first=False, meta_shacl=False, debug=False)
# if not r[0]:
#     print(r[2])
#     sys.exit(1)
# else:
#     print("Conforms\n " + str(r[0]))

