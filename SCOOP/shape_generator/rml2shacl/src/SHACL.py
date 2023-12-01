import rdflib
import pprint
from pyshacl import validate


class SHACL:
    def __init__(self):
        self.graph = rdflib.Graph()
        self.results_text = ''
        self.results_graph = None
        self.conforms = False

    def printGraph(self, keuze, graph):
        if keuze == 1:
            for stmt in graph:
                print("SHACL:" + str(stmt))
        else:
            for stmt in graph:
                pprint.pprint(stmt)

    def Validation(self, graph, data_graph):

        validate

        r = validate(data_graph, shacl_graph=graph, ont_graph=None,
                     inference='rdfs', abort_on_first=False, meta_shacl=False, debug=False)
        self.conforms, self.results_graph, self.results_text = r
        # results_graph is RDF graph of the validation report
        # results_text is the validation report in text
        # self.printGraph(1,results_graph)
        # print(self.results_text)
