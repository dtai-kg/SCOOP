import pprint
from typing import Dict, Optional, Type

import rdflib
from rdflib.graph import Graph
from rdflib.term import BNode, Identifier, URIRef
from .rml_model import (
    GraphMap,
    LogicalSource,
    ObjectMap,
    PredicateMap,
    PredicateObjectMap,
    SubjectMap,
    TermMap,
    TriplesMap,
)


class RML:
    def __init__(self):
        self.graph = rdflib.Graph()
        self.rmlNS = rdflib.Namespace('http://semweb.mmlab.be/ns/rml#')
        self.r2rmlNS = rdflib.Namespace('http://www.w3.org/ns/r2rml#')
        self.TEMPLATE = self.r2rmlNS.template
        self.REFERENCE = self.rmlNS.reference
        self.TERMTYPE = self.r2rmlNS.termType
        self.POM = self.r2rmlNS.predicateObjectMap
        self.PREDICATE = self.r2rmlNS.predicate
        self.PRED_MAP = self.r2rmlNS.predicateMap
        self.TRIPLES_MAP_CLASS = self.r2rmlNS.TriplesMap
        self.SUBJECT_MAP = self.r2rmlNS.subjectMap
        self.CLASS = self.r2rmlNS['class']
        self.OJBECT_MAP = self.r2rmlNS.objectMap
        self.IRI_CLASS = self.r2rmlNS.IRI
        self.LANGUAGE = self.r2rmlNS.language
        self.CONSTANT = self.r2rmlNS.constant
        self.OBJECT = self.r2rmlNS.object
        self.DATATYPE = self.r2rmlNS.datatype
        self.LOGICAL_SOURCE = self.rmlNS.logicalSource
        self.LOGICAL_TABLE = self.r2rmlNS.logicalTable

        # contains triple maps models from rml_model module 
        # the keys are the triples maps' IRI values 
        self.tm_model_dict: Dict[Identifier, TriplesMap] = dict()
        self.graphs = []
        self.refgraphs = []

    def printGraph(self, keuze):
        if keuze == 1:
            for stmt in self.graph:
                print(stmt)
        else:
            for stmt in self.graph:
                pprint.pprint(stmt)

    def parseFile(self, file_name):
        self.graph.parse(file_name, format=rdflib.util.guess_format(file_name))
        self.tm_model_dict = self.parseTriplesMaps(self.graph)

    def printQuery(self, graph, query):
        print("\n".join([f"{s}, {p}, {o}" for s, p, o in graph.triples(query)]))

    def parseTriplesMaps(self, graph: Graph) -> Dict[Identifier, TriplesMap]:

        tms = dict()
        tm_tmclass = {iri for iri, _, _ in graph.triples((None, None, self.TRIPLES_MAP_CLASS))}
        tm_logical_source = {iri for iri, _, _ in graph.triples((None, self.LOGICAL_SOURCE, None))}
        tm_logical_table = {iri for iri, _, _ in graph.triples((None, self.LOGICAL_TABLE, None))}
        tm_iri_set = tm_tmclass | tm_logical_source | tm_logical_table

        for tm_iri in tm_iri_set:

            # loop through the triples of the TriplesMap with IRI  == tm_iri 
            # this loop will parse the corresponding subject maps and POMs for the 
            # given TriplesMaps IRI. 

            sm = None
            poms = []
            gm = None
            logical_source = None

            sm = self.parseTermMapfromParentTermMap(tm_iri, self.r2rmlNS.subject, self.SUBJECT_MAP, graph, SubjectMap)

            for source_predicate in [self.LOGICAL_SOURCE, self.LOGICAL_TABLE]:
                try:
                    _, _, logical_source_iri = next(graph.triples((tm_iri, source_predicate, None)))
                except StopIteration as e:
                    continue

            logical_source = self.parseLogicalSource(logical_source_iri, graph)

            for _, _, pom_iri in graph.triples((tm_iri, self.POM, None)):
                pom = self.parsePredicateObjectMap(pom_iri, graph)
                poms.append(pom)

            tms[tm_iri] = TriplesMap(tm_iri, sm, poms, logical_source, gm)

        return tms

    def parseTermMapfromParentTermMap(self,
                                      parent_iri: Identifier, constant_pred: URIRef,
                                      map_pred: URIRef, graph: Graph,
                                      class_cons: Type[TermMap]) -> Optional[TermMap]:
        """
        Parses a TermMap from its parent TermMap identified with the given IRI value. 
        This function expands the shorthand version to a more explicit term map. 
        i.e ?x rr:predicate ?y.  -> ?x rr:predicateMap [ rr:constant ?y ]. 
        The type of TermMap parsed will be determined by the parameters: 
        constant_pred, map_red, map_parser, and class_cons
        """

        default_val = (None, None, None)

        # Check if an explicit term map exists and parse them
        _, _, term_iri = next(graph.triples((parent_iri, map_pred, None)), default_val)
        if not term_iri is None:
            return self.parseTermMap(term_iri, graph, class_cons)
            # End of explicit term map parsing

        # Check if a shorthand term map (constant shortcut) exists and parse it
        _, _, const_iri = next(graph.triples((parent_iri, constant_pred, None)), default_val)
        if const_iri is None:
            return None
        po_dict = {
            self.CONSTANT: [const_iri]
        }
        return class_cons(iri=BNode(), po_dict=po_dict)

    def parseTermMap(self, sub_node: Identifier, graph: Graph, class_cons: Type[TermMap]) -> Optional[TermMap]:
        """
        Parses a TermMap identified by the given subject node. 
        The associated GraphMap will also be parsed and added to the generated TermMap automatically. 
        """
        po_dict = dict()
        for _, p, o in graph.triples((sub_node, None, None)):
            if not p in po_dict:
                po_dict[p] = []
            po_dict[p].append(o)

            # Parse a graph map if it exists
        graphMap = self.parseTermMapfromParentTermMap(
            sub_node, self.r2rmlNS.graph, self.r2rmlNS.graphMap, graph, GraphMap)

        po_dict.pop(self.r2rmlNS.graph, None)
        po_dict[self.r2rmlNS.graphMap] = [graphMap]

        return class_cons(sub_node, po_dict)

    def parseLogicalSource(self, logs_iri: Identifier, graph: Graph) -> LogicalSource:
        po_dict = dict()

        for _, p, o in graph.triples((logs_iri, None, None)):
            po_dict[p] = o
        return LogicalSource(logs_iri, po_dict)

    def parsePredicateObjectMap(self, pom_iri: Identifier, graph: Graph) -> PredicateObjectMap:

        graphMap = self.parseTermMapfromParentTermMap(
            pom_iri, self.r2rmlNS.graph, self.r2rmlNS.graphMap,
            graph, GraphMap)
        predicateMap = self.parseTermMapfromParentTermMap(
            pom_iri, self.PREDICATE, self.PRED_MAP,
            graph, PredicateMap)
        objectMap = self.parseTermMapfromParentTermMap(
            pom_iri, self.OBJECT, self.OJBECT_MAP,
            graph, ObjectMap)

        return PredicateObjectMap(pom_iri, {self.r2rmlNS.graphMap: [graphMap]}, predicateMap, objectMap)


    def removeBlankNodesMultipleMaps(self):
        # loop over all the Triple Maps in the RML input file
        for sTM, pTM, oTM in self.graph.triples((None, None, self.r2rmlNS.TriplesMap)):
            graphHelp = {}
            graphsPOM = []
            graphTripleMap = rdflib.Graph()
            graphsubjectMap = rdflib.Graph()
            graphlogicalSource = rdflib.Graph()
            graphTripleMap.add((sTM, pTM, oTM))  # add triplesmap header
            graphHelp["TM"] = graphTripleMap
            tel = 0
            # inside one Triple Map we doe loops over:
            for s, p, o in self.graph.triples((sTM, None, None)):
                # the triples belonging to the Logical Source
                if p == self.rmlNS.logicalSource:
                    for s2, p2, o2 in self.graph.triples((o, None, None)):
                        # searching for same Blank Node
                        # add logical source info
                        graphlogicalSource.add((p, p2, o2))
                    graphHelp["LS"] = graphlogicalSource
                # the triples belonging to the Subject Map
                if p == self.SUBJECT_MAP:
                    for s2, p2, o2 in self.graph.triples((o, None, None)):
                        # searching for same Blank Node
                        graphsubjectMap.add((p, p2, o2))
                    # add subject Map  info
                    graphHelp["SM"] = graphsubjectMap
                # the multiple triples that are PredicateObject Maps
                if p == self.POM:
                    graphPredicatObjectMap = rdflib.Graph()
                    # searching for one PredicatObjectMap
                    # searching for same Blank Node
                    for s2, p2, o2 in self.graph.triples((o, None, None)):
                        if p2 == self.r2rmlNS.predicateMap:
                            for s3, p3, o3 in self.graph.triples((o2, self.CONSTANT, None)):
                                # we make the "rr:predicateMap rr:constant o" triple to sthe shurtcut "rr:PredicateObjectMap rr:predicate o2"
                                graphPredicatObjectMap.add((p, self.PREDICATE, o3))
                        # add the predicateobjectMap with the constant transformed into rr:predicate instead of constant
                        else:
                            graphPredicatObjectMap.add((p, p2, o2))
                        # add the predicateobjectMap
                    # searching for which objectMap belongs to this PredicateObjectMap
                    for s2, p2, o2 in graphPredicatObjectMap.triples((p, self.OJBECT_MAP, None)):
                        for s3, p3, o3 in self.graph.triples((o2, None, None)):
                            graphPredicatObjectMap.add((p2, p3, o3))
                        # add the objectMap beloning to the predicateobjectMap added in previous loop
                        graphPredicatObjectMap.remove((s2, p2, o2))
                    # remove something with a blanknode in that we added too much
                    # if we don't have an rr:ObjectMap but an rr:object (as part of rr:predicateMap as an predicate)
                    # we will write this as rr:ObjectMap rr:constant (object that belonged to the rr:object)
                    for s2, p2, o2 in graphPredicatObjectMap.triples((p, self.OBJECT, None)):
                        # graphPredicatObjectMap.add((s2,p2,o2))
                        # #add the object beloning to the predicateobjectMap added in previous loop
                        graphPredicatObjectMap.add((self.OJBECT_MAP, self.CONSTANT, o2))
                        graphPredicatObjectMap.remove((s2, p2, o2))
                    # remove the "rr:predicateMap rr:object o2" triple from the graph because it gets added in loop for objectMap
                    # loop to find any possible RefObjectMaps
                    for sROM, pROM, oROM in self.graph.triples((None, None, self.r2rmlNS.RefObjectMap)):
                        # if we find one we see if it belongs to the ObjectMap we are working with now
                        for s3, p3, o3 in self.graph.triples((p, self.OJBECT_MAP, sROM)):
                            # if this is the fact we search inside the RefObjectMap (sROM) for the value of rr:parentTriplesMap
                            for s4, p4, o4 in self.graph.triples((sROM, self.r2rmlNS.parentTriplesMap, None)):
                                graphPredicatObjectMap.add(
                                    (self.OJBECT_MAP, self.r2rmlNS.parentTriplesMap, o4))
                    # add the parentTriplesMap to the ObjectMap

                    graphHelp["POM" + str(tel)] = graphPredicatObjectMap
                    tel = tel + 1
            self.graphs.append(graphHelp)




if __name__ == '__main__':
    Rml = RML()
    Rml.parseFile("mapping.ttl")
