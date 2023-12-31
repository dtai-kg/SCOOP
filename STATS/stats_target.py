import rdflib
from rdflib import Graph, URIRef, Literal, BNode, Namespace, RDF
import os
import sys

class STATS:
    def __init__(self, output_file):
        self.shaclNS = Namespace('http://www.w3.org/ns/shacl#')
        self.output = output_file
        self.f = open(self.output, "w")

        self.valueTypeConstraints = [self.shaclNS["class"], self.shaclNS.datatype, self.shaclNS.nodeKind]
        self.cardinalityConstraints = [self.shaclNS.minCount, self.shaclNS.maxCount]
        self.valueRangeConstraints = [self.shaclNS.minExclusive, self.shaclNS.minInclusive, self.shaclNS.maxExclusive, self.shaclNS.maxInclusive]
        self.stringBasedConstraints = [self.shaclNS.minLength, self.shaclNS.maxLength, self.shaclNS.pattern, self.shaclNS.languageIn, self.shaclNS.uniqueLang]
        self.propertyPairConstraints = [self.shaclNS.equals, self.shaclNS.disjoint, self.shaclNS.lessThan, self.shaclNS.lessThanOrEquals]
        self.logicalConstraints = [self.shaclNS["and"], self.shaclNS["or"], self.shaclNS.xone, self.shaclNS["not"]]
        self.shapeBasedConstriants = [self.shaclNS.node, self.shaclNS.property, self.shaclNS.qualifiedValueShape, self.shaclNS.qualifiedMinCount,self.shaclNS.qualifiedMaxCount]
        self.otherConstraints = [self.shaclNS.closed, self.shaclNS.ignoredProperties, self.shaclNS.hasValue, self.shaclNS["in"], self.shaclNS.name, self.shaclNS.description]
        
        self.VT, self.CD, self.VR, self.SR, self.PP, self.LG, self.SA, self.OT = set(), set(), set(), set(), set(), set(), set(), set()
    
    def analyse_constraints(self, g):
        for s, p, o in g:
            if p in self.valueTypeConstraints:
                self.VT.add(p)
            elif p in self.cardinalityConstraints:
                self.CD.add(p)
            elif p in self.valueRangeConstraints:
                self.VR.add(p)
            elif p in self.stringBasedConstraints:
                self.SR.add(p)
            elif p in self.propertyPairConstraints:
                self.PP.add(p)
            elif p in self.logicalConstraints:
                self.LG.add(p)
            elif p in self.shapeBasedConstriants:
                self.SA.add(p)
            elif p in self.otherConstraints:
                self.OT.add(p)

    
    
    def getGroundTruth(self, class_file, property_file):
        self.ground_truth_class = set()
        self.ground_truth_property = set()
        with open(class_file) as f:
            for line in f:
                self.ground_truth_class.add(line.strip())
        with open(property_file) as f:
            for line in f:
                self.ground_truth_property.add(line.strip())
        
        self.f.write(f"Ground Truth has {len(self.ground_truth_class)} classes and {len(self.ground_truth_property)} properties\n")

    def getPredicted(self, shacl_files):
        self.predicted_class, self.predicted_property = set(), set()
        for shacl_file in shacl_files:
            self.predictedGraph = Graph().parse(shacl_file)
            for s, _, o in self.predictedGraph.triples((None, self.shaclNS.targetClass, None)):
                self.predicted_class.add(str(o))
                for _,_,property in self.predictedGraph.triples((s,self.shaclNS.path,None)):
                    if property != RDF.type:
                        self.predicted_property.add(str(property))
                for _,_,property_node in self.predictedGraph.triples((s,self.shaclNS.property,None)):
                    for _,_,property in self.predictedGraph.triples((property_node,self.shaclNS.path,None)):
                        if property != RDF.type:
                            self.predicted_property.add(str(property))

            for _, _, o in self.predictedGraph.triples((None, self.shaclNS.targetSubjectsOf, None)):
                if o != RDF.type:
                    self.predicted_property.add(str(o))
                    for _,_,property in self.predictedGraph.triples((s,self.shaclNS.path,None)):
                        if property != RDF.type:
                            self.predicted_property.add(str(property))
                    for _,_,property_node in self.predictedGraph.triples((s,self.shaclNS.property,None)):
                        for _,_,property in self.predictedGraph.triples((property_node,self.shaclNS.path,None)):
                            if property != RDF.type:
                                self.predicted_property.add(str(property))
                            
            for _, _, o in self.predictedGraph.triples((None, self.shaclNS.targetObjectsOf, None)):
                if o != RDF.type:
                    self.predicted_property.add(str(o))
                    for _,_,property in self.predictedGraph.triples((s,self.shaclNS.path,None)):
                        if property != RDF.type:
                            self.predicted_property.add(str(property))
                    for _,_,property_node in self.predictedGraph.triples((s,self.shaclNS.property,None)):
                        for _,_,property in self.predictedGraph.triples((property_node,self.shaclNS.path,None)):
                            if property != RDF.type:    
                                self.predicted_property.add(str(property))
            self.analyse_constraints(self.predictedGraph)
        self.f.write(f"Predicted has {len(self.predicted_class)} classes and {len(self.predicted_property)} properties\n")
        self.f.write("VT, CD, VR, SR, PP, LG, SA, OT\n")
        self.f.write(f"{len(self.VT)}/{len(self.valueTypeConstraints)}, {len(self.CD)}/{len(self.cardinalityConstraints)}, {len(self.VR)}/{len(self.valueRangeConstraints)}, {len(self.SR)}/{len(self.stringBasedConstraints)}, {len(self.PP)}/{len(self.propertyPairConstraints)}, {len(self.LG)}/{len(self.logicalConstraints)}, {len(self.SA)}/{len(self.shapeBasedConstriants)}, {len(self.OT)}/{len(self.otherConstraints)}\n")
        self.f.write(f"{len(self.VT)}, {len(self.CD)}, {len(self.VR)}, {len(self.SR)}, {len(self.PP)}, {len(self.LG)}, {len(self.SA)}, {len(self.OT)}\n")
        
        self.f.write(f"VT: {self.VT}\n, CD: {self.CD}\n, VR: {self.VR}\n, SR: {self.SR}\n, PP: {self.PP}\n, LG: {self.LG}\n, SA: {self.SA}\n, OT: {self.OT}\n")
        

    def get_differ(self):
        # get difference classes and properties
        self.f.write(f"Classes in ground truth but not in predicted: {self.ground_truth_class.difference(self.predicted_class)}\n")
        self.f.write(f"Classes in predicted but not in ground truth: {self.predicted_class.difference(self.ground_truth_class)}\n")
        self.f.write(f"Properties in ground truth but not in predicted: {self.ground_truth_property.difference(self.predicted_property)}\n")
        self.f.write(f"Properties in predicted but not in ground truth: {self.predicted_property.difference(self.ground_truth_property)}\n")

   
    def cal_recall(self):

        self.f.write(f"Recall for classes: {len(self.ground_truth_class.intersection(self.predicted_class))/len(self.ground_truth_class)}\n")
        self.f.write(f"Recall for properties: {len(self.ground_truth_property.intersection(self.predicted_property))/len(self.ground_truth_property)}\n")


    def cal_precision(self):
        self.f.write(f"Precision for classes: {len(self.ground_truth_class.intersection(self.predicted_class))/len(self.predicted_class)}\n")
        self.f.write(f"Precision for properties: {len(self.ground_truth_property.intersection(self.predicted_property))/len(self.predicted_property)}\n")


    def cal_F1score(self):
        self.f.write(f"F1 score for classes: {2*len(self.ground_truth_class.intersection(self.predicted_class))/(len(self.ground_truth_class)+len(self.predicted_class))}\n")
        self.f.write(f"F1 score for properties: {2*len(self.ground_truth_property.intersection(self.predicted_property))/(len(self.ground_truth_property)+len(self.predicted_property))}\n")

    def writeName(self, name):
        self.f.write(f"================Start calculating {name}\n")

    def clean(self):
        self.predicted_class, self.predicted_property = set(), set()
        self.VT, self.CD, self.VR, self.SR, self.PP, self.LG, self.SA, self.OT = set(), set(), set(), set(), set(), set(), set(), set()

    def closeF(self):
        self.f.close()
        
    def basicStats(self, graph1, graph2):
        self.graph1 = Graph().parse(graph1)
        self.graph2 = Graph().parse(graph2)

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


if __name__ == "__main__":

    stats = STATS("STATS/log_target.txt")
    stats.getGroundTruth("STATS/FR.classes.txt", "STATS/FR.properties.txt")

    shacl_list = os.listdir("STATS")
    for shacl_file in shacl_list:
        if shacl_file.endswith(".ttl"):
            
            print("================Start calculating", shacl_file)
            stats.writeName(shacl_file)
            stats.getPredicted([os.path.join("STATS", shacl_file)])
            stats.cal_recall()
            stats.cal_precision()
            #stats.cal_accuracy()
            stats.cal_F1score()
            stats.get_differ()
            
            stats.clean()

    
    print("================Start calculating", "STATS/temp/owl0.ttl")
    stats.writeName("STATS/temp/owl0.ttl")
    stats.getPredicted(["STATS/temp/owl0.ttl"])
    stats.cal_recall()
    stats.cal_precision()
   # stats.cal_accuracy()
    stats.cal_F1score()
    stats.get_differ()
    
    stats.clean()

    
    print("================Start calculating", "STATS/temp/owl0.ttl")
    stats.writeName("STATS/temp/xsd0.ttl")
    stats.getPredicted(["STATS/temp/xsd0.ttl"])
    stats.cal_recall()
    stats.cal_precision()
    #stats.cal_accuracy()
    stats.cal_F1score()
    stats.get_differ()
    
    stats.clean()

    shacl_list = os.listdir("STATS/temp")
    rml_list = []
    for shacl_file in shacl_list:
        if "rml" in shacl_file:
            rml_list.append(os.path.join("STATS/temp", shacl_file))

    print("================Start calculating", "RML_LIST")
    stats.writeName("RML_LIST")
    stats.getPredicted(rml_list)
    stats.cal_recall()
    stats.cal_precision()
    stats.cal_F1score()
    #stats.cal_accuracy()
    stats.get_differ()
    
    stats.clean()

    stats.closeF()
    
