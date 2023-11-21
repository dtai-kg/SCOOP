import rdflib
from rdflib import Graph, URIRef, Literal, BNode, Namespace, RDF
import os

def getClassProperty(graph):
    shaclNS = Namespace('http://www.w3.org/ns/shacl#')
    class_set = set()
    property_set = set()
    for _, _, o in graph.triples((None, shaclNS.targetClass, None)):
        class_set.add(o)
    for _, _, o in graph.triples((None, shaclNS.path, None)):
        if o != RDF.type:
            property_set.add(o)
    print(f"Graph has {len(class_set)} classes and {len(property_set)} properties")
    return len(class_set), (property_set)

class STATS:
    def __init__(self, graph1, graph2):
        self.shaclNS = Namespace('http://www.w3.org/ns/shacl#')

        self.graph1 = Graph().parse(graph1)
        self.graph2 = Graph().parse(graph2)

    def basicStats(self):
        self.graph1_class, self.graph2_class, self.graph1_property, self.graph2_property = set(), set(), set(), set()
        for _, _, o in self.graph1.triples((None, self.shaclNS.targetClass, None)):
            self.graph1_class.add(o)
        for _, _, o in self.graph2.triples((None, self.shaclNS.targetClass, None)):
            self.graph2_class.add(o)
        for _, _, o in self.graph1.triples((None, self.shaclNS.path, None)):
            if o != RDF.type:
                self.graph1_property.add(o)
        for _, _, o in self.graph2.triples((None, self.shaclNS.path, None)):
            if o != RDF.type:
                self.graph2_property.add(o)

        print(f"Graph1 has {len(self.graph1_class)} classes and {len(self.graph1_property)} properties")
        print(f"Graph2 has {len(self.graph2_class)} classes and {len(self.graph2_property)} properties")


    def commenStats(self):
        differ_classes = self.graph1_class.difference(self.graph2_class)
        print(f"Graph1 has {len(differ_classes)} more classes than Graph2")
        for c in differ_classes:
            print("\t",c)
        differ_classes = self.graph2_class.difference(self.graph1_class)
        for c in differ_classes:
            print("\t",c)
        print(f"Graph2 has {len(differ_classes)} more classes than Graph1")

        differ_properties = self.graph1_property.difference(self.graph2_property)
        print(f"Graph1 has {len(differ_properties)} more properties than Graph2")
        for p in differ_properties:
            print("\t",str(p).split("/")[-1])
        differ_properties = self.graph2_property.difference(self.graph1_property)
        print(f"Graph2 has {len(differ_properties)} more properties than Graph1")
        for p in differ_properties:
            print("\t",str(p).split("/")[-1])

# print(f"Shape {} has {} Node Shape and {} Property Shape")
# print(f"Shape {} has {} more classes that shape {}")
# print(f"Shape {} has {} more properties that shape {}")
# print(f"Shape {} covers constriants {}")


if __name__ == "__main__":

    # Graph1 = "STATS/integration_rml_xsd.ttl"
    Graph1 = "STATS/integration_rml_xsd_owl.ttl"
    Graph2 = "STATS/temp/owl0.ttl"
    #Graph2 = "STATS/all_countries_combined_QSE_0.1_100_SHACL.ttl"
    print(f"Graph1: {Graph1}")
    print(f"Graph2: {Graph2}")

    stats = STATS(Graph1, Graph2)
    stats.basicStats()
    stats.commenStats()

    # print("Start STATS for RML2SHACL")
    # g = Graph()
    # rml_list_path = "STATS/temp"
    # rml_list = os.listdir(rml_list_path)
    # rml_list = [os.path.join(rml_list_path, rml) for rml in rml_list if rml.endswith(".ttl")]
    # for file in rml_list:
    #     if "rml" in file:
    #         g.parse(file, format="turtle")
    # getClassProperty(g)

    # print("Start STATS for Astrea")
    # g = Graph().parse("STATS/temp/owl0.ttl")
    # getClassProperty(g)

    # print("Start STATS for Adjusted XSD2SHACL")
    # g = Graph().parse("STATS/temp/xsd0.ttl")
    # getClassProperty(g)
