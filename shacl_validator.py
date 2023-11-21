from pyshacl import validate
import rdflib
from rdflib import Graph

# # Load the data
data = rdflib.Graph().parse("LT_MT.ttl", format="ttl")

# Load the shape graph
sg = rdflib.Graph().parse("STATS/integration_rml_xsd.ttl", format="ttl")

# Perform validation
r = validate(data_graph=data, shacl_graph=sg)
conforms, results_graph, results_text = r
print("Conforms\n " + str(conforms))
print("Results Graph\n" + str(results_graph.serialize(format="turtle")))
print("Results Text\n" + results_text)

# validation_shape_graph = Graph().parse("shacl-shacl.ttl", format="turtle")
# # sg = rdflib.Graph().parse("STATS/all_countries_combined_QSE_0.1_100_SHACL.ttl", format="ttl")
# r = validate(sg, shacl_graph=validation_shape_graph, ont_graph=None,
#                 inference='rdfs', abort_on_first=False, meta_shacl=False, debug=False)
# if not r[0]:
#     print(r[2])
#     sys.exit(1)