from pyshacl import validate
import rdflib
from rdflib import Graph, Namespace
import os
import sys

print("Loading RDF file...")
rdf_path = "STATS/validation/"
rdf_data="MT.ttl"
data_graph = rdflib.Graph().parse(rdf_path+rdf_data, format="ttl")
print("RDF file loaded.")

sg = rdflib.Graph().parse("temp/owl0.ttl", format="ttl")

r = validate(data_graph=data_graph, shacl_graph=sg)
conforms, results_graph, results_text = r
print("Conforms\n " + str(conforms))
results_graph.serialize(destination="STATS/validation/owl0.ttl.MT.validation.ttl", format='turtle')
sys.exit(1)

for shacl_file in os.listdir("STATS/"):
    if "integration" in shacl_file:
        print("Validating", shacl_file)
        try:
            sg = rdflib.Graph().parse("STATS/"+shacl_file, format="ttl")

            r = validate(data_graph=data_graph, shacl_graph=sg)
            conforms, results_graph, results_text = r
            print("Conforms\n " + str(conforms))
            results_graph.serialize(destination="STATS/validation/"+shacl_file+".MT.validation.ttl", format='turtle')
        except:
            print("Error validating", shacl_file)
            

for shacl_file in os.listdir("STATS/temp"):
    if shacl_file.endswith(".ttl"):
        print("Validating", shacl_file)
        try:
            sg = rdflib.Graph().parse("STATS/temp/"+shacl_file, format="ttl")

            r = validate(data_graph=data_graph, shacl_graph=sg)
            conforms, results_graph, results_text = r
            print("Conforms\n " + str(conforms))
            results_graph.serialize(destination="STATS/validation/temp/"+shacl_file+".MT.validation.ttl", format='turtle')
        except:
            print("Error validating", shacl_file)




# validation_shape_graph = Graph().parse("shacl-shacl.ttl", format="turtle")
# #sg = rdflib.Graph().parse("STATS/all_countries_combined_QSE_0.1_100_SHACL.ttl", format="ttl")
# r = validate(sg, shacl_graph=validation_shape_graph, ont_graph=None,
#                 inference='rdfs', abort_on_first=False, meta_shacl=False, debug=False)
# if not r[0]:
#     print(r[2])
#     sys.exit(1)
# else:
#     print("Conforms\n " + str(r[0]))

