import os
import sys
from pathlib import Path
from typing import List, Dict
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from pyshacl import validate
import random


class ShapeIntegrationPriority():
    def __init__(self, shapes: List, output: str):
        self.shaclNS = Namespace('http://www.w3.org/ns/shacl#')
        self.rdfSyntax = Namespace(
            'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.targetDeclarationNS = [self.shaclNS.targetClass, self.shaclNS.targetNode, self.shaclNS.targetSubjectsOf, self.shaclNS.targetObjectsOf]
        self.propertyPathNS = [self.shaclNS.path]
        self.shapes = shapes
        self.output = output
        self.SHACL = Graph()

        self.integrated_identifier = []
        self.random_number = [random.randint(1000, 9999) for i in range(1000)]
    
    def integration(self):
        """
        Integrating a set of shapes into a single shape
        """
        for shape_add, _ in self.shapes:

            NodeShapes_current, _ = self.getNodeShapes(self.SHACL)
            NodeShapes_add, shape_add = self.getNodeShapes(shape_add, replace=True)
            self.integrated_identifier.extend(NodeShapes_add)

            # Get target declaration for a given shape, return a dictionary with target term and object value as key, identifier with involved property paths as value
            target_current = self.getTargetDeclaration(self.SHACL, NodeShapes_current)
            target_add = self.getTargetDeclaration(shape_add, NodeShapes_add)

            if len(target_current) == 0:
                self.SHACL = shape_add
                continue

            # Calculate the common targets and different targets in current shape and the shap that is going to be added
            common_targets = set(target_current.keys()).intersection(set(target_add.keys()))
            differ_targets = set(target_add.keys()).difference(set(target_current.keys()))

            # Add possible extra constriants for the common targets
            for target, target_value in common_targets:
                identifiers_current =  list(target_current[(target, target_value)].keys())
                identifiers_add =  list(target_add[(target, target_value)].keys())
                
                for identifier_current in identifiers_current:
                    constraints_current = self.getConstraints(self.SHACL, identifier_current, NodeShapes_current)
                    path_current = target_current[(target, target_value)][identifier_current]
                    # print("identifier_current: ", identifier_current)                   
                    for identifier_add in identifiers_add:
                        constraints_add = self.getConstraints(shape_add, identifier_add, NodeShapes_add)
                        # Add constraints in the shape that has target declaration
                        for constraint_add, constraint_add_value in constraints_add.items():
                            # print("constraint_add: ", constraint_add, constraint_add_value)
                            if constraint_add_value == constraints_current.get(constraint_add, None):
                                continue
                            else:
                                self.addConstraints(shape_add, identifier_current, constraints_current, constraint_add, constraint_add_value)
                        
                        path_add = target_add[(target, target_value)][identifier_add]
                        common_paths = set(path_current.keys()).intersection(set(path_add.keys()))
                        differ_paths = set(path_add.keys()).difference(set(path_current.keys()))

                        for path, path_value in common_paths:

                            identifiers_path_current =  path_current[(path, path_value)]
                            identifiers_path_add =  path_add[(path, path_value)]

                            for identifier_path_current in identifiers_path_current:
                                constraints_current = self.getConstraints(self.SHACL, identifier_path_current, NodeShapes_current)
                                
                                for identifier_path_add in identifiers_path_add:
                                    
                                    constraints_add = self.getConstraints(shape_add, identifier_path_add, NodeShapes_add)
                                    # Add constraints in the shape that has property path
                                    for constraint_add, constraint_add_value in constraints_add.items():
                                        if constraint_add_value == constraints_current.get(constraint_add, None):
                                            continue
                                        else:
                                            self.addConstraints(shape_add, identifier_path_current, constraints_current, constraint_add, constraint_add_value)
                        
                        for path, path_value in differ_paths:
                            # TODO: Double check if this is correct
                            identifiers_path_add =  path_add[(path, path_value)]
                            for identifier_path_add in identifiers_path_add:
                                self.addShape(shape_add, identifier_path_add)
                                self.SHACL.add((identifier_current, self.shaclNS["property"], identifier_path_add))
                                            
            for target, target_value in differ_targets:
                identifiers_add =  list(target_add[(target, target_value)].keys())

                if target == self.shaclNS.targetClass or target == self.shaclNS.targetNode:
                    for identifier_add in identifiers_add:
                        self.addShape(shape_add, identifier_add)

                elif target == self.shaclNS.targetSubjectsOf:
                    # TODO NS+PS conflict checking
                    for identifier_add in identifiers_add:
                        self.addShape(shape_add, identifier_add)
                elif target == self.shaclNS.targetObjectsOf:
                    # TODO PS conflict checking
                    for identifier_add in identifiers_add:
                        self.addShape(shape_add, identifier_add)

        self.writeShapeToFile()

    def getTargetDeclaration(self, shape: Graph, NodeShapes: List):
        targetDict = {}
        
        for identifier, p, o in shape:
            if p in self.targetDeclarationNS:
                l = targetDict.get((p,o),{})
                l[identifier] = self.getPropertyPath(l.get(identifier,{}),shape,identifier, NodeShapes)
                targetDict[(p,o)] = l
        return targetDict

    def getPropertyPath(self, propertyPaths: Dict, shape: Graph, identifier, NodeShapes: List):
        for s, p, o in shape.triples((identifier, None, None)):     
            if p in self.propertyPathNS:
                l = propertyPaths.get((p,o),[])
                l.append(s)
                propertyPaths[(p,o)] = l
            elif p == self.shaclNS["property"]:
                propertyPaths = self.getPropertyPath(propertyPaths, shape, o, NodeShapes)
            elif (s in NodeShapes) and (p == self.shaclNS.node):
                propertyPaths = self.getPropertyPath(propertyPaths, shape, o, NodeShapes)
        return propertyPaths

    def getNodeShapes(self, shape: Graph, replace=False):
        NodeShapes = []
        if replace == False:
            for s, p, o in shape.triples((None, self.rdfSyntax.type, self.shaclNS.NodeShape)):
                NodeShapes.append(s)
        else:
            # repalce duplicate node shapes in previous shape
            for s, p, o in shape.triples((None, self.rdfSyntax.type, self.shaclNS.NodeShape)):
                if s not in self.integrated_identifier:
                    NodeShapes.append(s)
                else:
                    new_shape_identifier = URIRef(str(s)+str(self.random_number.pop()))
                    shape = self.updateShape(shape, s, new_shape_identifier)

        return NodeShapes, shape

    def updateShape(self, g, shape_identifier, new_shape_identifier):
        for s, p, o in g.triples((shape_identifier,None,None)):
            g.remove((s,p,o))
            g.add((new_shape_identifier,p,o))
        for s, p, o in g.triples((None,None,shape_identifier)):
            g.remove((s,p,o))
            g.add((s,p,new_shape_identifier)) 
        return g

    def getConstraints(self, shape: Graph, identifier, NodeShapes: List):
        constraints = {}
        for s, p, o in shape.triples((identifier, None, None)):
            if p == self.shaclNS.node:
                if s not in NodeShapes:
                    constraints[p] = o
            elif (p not in [self.rdfSyntax.type, self.shaclNS["property"]]) and (p not in self.targetDeclarationNS) and (p not in self.propertyPathNS):
                constraints[p] = o
        return constraints

    def addConstraints(self, shape_add, identifier_path_current, constraints_current, constraint_add, constraint_add_value):
        self.conflictChecking(shape_add, identifier_path_current, constraints_current, constraint_add, constraint_add_value)
            # self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))

    def conflictChecking(self, shape_add, identifier_path_current, constraints_current, constraint_add, constraint_add_value):
        # Check if the constraint that is going to be added is conflict with the current constraints
        # Wrong: Conflict checking: checking whether the added constraint (already exsit) will cause the conform result to violation
        # Conflict checking: 
        if constraint_add == self.shaclNS["class"]:
            self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
        
        elif constraint_add == self.shaclNS.nodeKind:
            if constraints_current.get(self.shaclNS.nodeKind, None) == None:
                # If there is no nodeKind in previous shape, need to check datatype also
                if constraint_add_value == self.shaclNS.Literal:
                    self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
                elif ("IRI" in str(constraint_add_value)) or ("BlankNode" in str(constraint_add_value)):
                    if constraints_current.get(self.shaclNS.datatype, None) == None:
                        self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
                    else:
                        return None
            elif constraints_current.get(self.shaclNS.nodeKind) == constraint_add_value:
                return None
            elif (constraints_current.get(self.shaclNS.nodeKind) == self.shaclNS.IRI) and ((constraint_add_value == self.shaclNS.BlankNodeOrIRI) or (constraint_add_value == self.shaclNS.IRIOrLiteral)):
                # TODO: discuss whether to add a more soft constraint, I prefer the strict option since we are expect to find more violations
                pass
        
        elif constraint_add == self.shaclNS.datatype:
            if constraints_current.get(self.shaclNS.datatype, None) == None:
                if constraints_current.get(self.shaclNS.nodeKind, None) == None:
                    self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
                elif "Literal" in str(constraints_current.get(self.shaclNS.nodeKind)):
                    self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
                else:
                    return None
            else:
                pass # TODO: Possible use sh:or to add more soft constraints
            
        elif constraint_add == self.shaclNS.minCount:
            if constraints_current.get(self.shaclNS.minCount, None) == None:
                if constraints_current.get(self.shaclNS.maxCount, None) == None:
                    self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
                elif constraint_add_value <= constraints_current.get(self.shaclNS.maxCount):
                    self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
            else:
                pass # TODO Discuss whether to add a more soft constraint?

        elif constraint_add == self.shaclNS.maxCount:
            if constraints_current.get(self.shaclNS.maxCount, None) == None:
                if constraints_current.get(self.shaclNS.minCount, None) == None:
                    self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
                elif constraint_add_value >= constraints_current.get(self.shaclNS.minCount):
                    self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
            else:
                pass # TODO Discuss whether to add a more soft constraint?

        elif constraint_add == self.shaclNS.minExclusive:
            if constraints_current.get(self.shaclNS.minExclusive, None) != None:
                pass
            elif (constraints_current.get(self.shaclNS.nodeKind, None) == None) or "Literal" in str(constraints_current.get(self.shaclNS.nodeKind, None)):
                if (constraints_current.get(self.shaclNS.maxExclusive, None) == None or constraint_add_value < constraints_current.get(self.shaclNS.maxExclusive, None)) and (constraints_current.get(self.shaclNS.maxInclusive, None) == None or constraint_add_value < constraints_current.get(self.shaclNS.maxInclusive, None)):
                    if "string" not in str(constraints_current.get(self.shaclNS.datatype, None)):
                        self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
                
        elif constraint_add == self.shaclNS.maxExclusive:
            if constraints_current.get(self.shaclNS.maxExclusive, None) != None:
                pass
            elif (constraints_current.get(self.shaclNS.nodeKind, None) == None) or "Literal" in str(constraints_current.get(self.shaclNS.nodeKind, None)):
                if (constraints_current.get(self.shaclNS.minExclusive, None) == None or constraint_add_value > constraints_current.get(self.shaclNS.minExclusive, None)) and (constraints_current.get(self.shaclNS.minInclusive, None) == None or constraint_add_value > constraints_current.get(self.shaclNS.minInclusive, None)):
                    if "string" not in str(constraints_current.get(self.shaclNS.datatype, None)):
                        self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))

        elif constraint_add == self.shaclNS.minInclusive:
            if constraints_current.get(self.shaclNS.minInclusive, None) != None:
                pass
            elif (constraints_current.get(self.shaclNS.nodeKind, None) == None) or "Literal" in str(constraints_current.get(self.shaclNS.nodeKind, None)):
                if (constraints_current.get(self.shaclNS.maxExclusive, None) == None or constraint_add_value < constraints_current.get(self.shaclNS.maxExclusive, None)) and (constraints_current.get(self.shaclNS.maxInclusive, None) == None or constraint_add_value <= constraints_current.get(self.shaclNS.maxInclusive, None)):
                    if "string" not in str(constraints_current.get(self.shaclNS.datatype, None)):
                        self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))

        elif constraint_add == self.shaclNS.maxInclusive:
            if constraints_current.get(self.shaclNS.maxInclusive, None) != None:
                pass
            elif (constraints_current.get(self.shaclNS.nodeKind, None) == None) or "Literal" in str(constraints_current.get(self.shaclNS.nodeKind, None)):
                if (constraints_current.get(self.shaclNS.minExclusive, None) == None or constraint_add_value > constraints_current.get(self.shaclNS.minExclusive, None)) and (constraints_current.get(self.shaclNS.minInclusive, None) == None or constraint_add_value >= constraints_current.get(self.shaclNS.minInclusive, None)):
                    if "string" not in str(constraints_current.get(self.shaclNS.datatype, None)):
                        self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))

        elif constraint_add == self.shaclNS.minLength:
            if constraints_current.get(self.shaclNS.minLength, None) != None:
                pass
            else:
                if constraints_current.get(self.shaclNS.maxLength, None) == None:
                    self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
                elif constraint_add_value <= constraints_current.get(self.shaclNS.maxLength):
                    self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
            
        elif constraint_add == self.shaclNS.maxLength:
            if constraints_current.get(self.shaclNS.maxLength, None) != None:
                pass
            else:
                if constraints_current.get(self.shaclNS.minLength, None) == None:
                    self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
                elif constraint_add_value >= constraints_current.get(self.shaclNS.minLength):
                    self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
            
        elif constraint_add == self.shaclNS.pattern:
            if constraints_current.get(self.shaclNS.pattern, None) != None:
                pass
            else:
                self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
        
        elif constraint_add == self.shaclNS.flags:
            if constraints_current.get(self.shaclNS.flags, None) != None:
                pass
            else:
                self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))

        elif constraint_add == self.shaclNS.languageIn:
            _, languageIn_add = self.findList(shape_add, constraint_add_value, [])
            if languageIn_add == []:
                return None

            if constraints_current.get(self.shaclNS.languageIn, None) != None:
                for s, p, o in self.SHACL.triples((identifier_path_current, self.shaclNS.languageIn, None)):    
                    node_current = o
                    break
                _, languageIn_current = self.findList(self.SHACL, node_current, [])
            else:
                node_current = BNode()
                self.SHACL.add((identifier_path_current, constraint_add, node_current))
                languageIn_current = []
            languageIn_merge = list(set(languageIn_current+languageIn_add))

            self.transformList(node_current, languageIn_merge)

        elif constraint_add == self.shaclNS.uniqueLang:
            if constraints_current.get(self.shaclNS.uniqueLang, None) != None:
                pass
            else:
                self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))

        elif constraint_add == self.shaclNS.equals:
            self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))

        elif constraint_add == self.shaclNS.disjoint:
            self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))

        elif constraint_add == self.shaclNS.lessThan:
            self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))

        elif constraint_add == self.shaclNS.lessThanOrEquals:
            self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))

        elif constraint_add == self.shaclNS["not"]:
            self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
            self.SHACL += self.extractSubgraph(shape_add, constraint_add_value)

        elif constraint_add == self.shaclNS["and"]:
            self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
            self.SHACL += self.extractSubgraph(shape_add, constraint_add_value)

        elif constraint_add == self.shaclNS["or"]:
            self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
            self.SHACL += self.extractSubgraph(shape_add, constraint_add_value)

        elif constraint_add == self.shaclNS.xone:
            self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
            self.SHACL += self.extractSubgraph(shape_add, constraint_add_value)

        elif constraint_add == self.shaclNS["node"]:
            self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))
            self.SHACL += self.extractSubgraph(shape_add, constraint_add_value)
        
        elif constraint_add == self.shaclNS.hasValue:
            self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))

        elif constraint_add == self.shaclNS["in"]:
            _, In_add = self.findList(shape_add, constraint_add_value, [])
            if In_add == []:
                return None

            if constraints_current.get(self.shaclNS["in"], None) != None:
                for s, p, o in self.SHACL.triples((identifier_path_current, self.shaclNS["in"], None)):
                    node_current = o
                    break
                _, In_current = self.findList(self.SHACL, node_current, [])
            else:
                node_current = BNode()
                self.SHACL.add((identifier_path_current, constraint_add, node_current))
                In_current = []
            In_merge = list(set(In_current+In_add))

            self.transformList(node_current, In_merge)
        else:
            self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))

    def findList(self, g, node_current, rdflist):
        for s, p, o in g.triples((node_current, None, None)):
            g.remove((s, p, o))
            if p == self.rdfSyntax.first:
                rdflist.append(o)
            elif p == self.rdfSyntax.rest:
                if o == self.rdfSyntax.nil:
                    continue
                else:
                    g, rdflist = self.findList(g, o, rdflist)
        return g, rdflist
      
    # Function copied from Thomas's code on GitHub
    # Source: https://github.com/RMLio/RML2SHACL
    def transformList(self, node, arr) -> None:
        """
        Transform the given array objects into RDF compliant array list. 
        The transformation is done in the manner of a functional list. 
        """
        current_node = node
        next_node = BNode()
        size = len(arr)
        for i, obj in enumerate(arr):

            self.SHACL.add(
                (current_node, self.rdfSyntax.first, obj))

            if i != size - 1:
                self.SHACL.add(
                    (current_node, self.rdfSyntax.rest, next_node))
            else:
                self.SHACL.add(
                    (current_node, self.rdfSyntax.rest, self.rdfSyntax.nil))
            current_node = next_node
            next_node = BNode()

    def addShape(self, shape_add, identifier_add):
        self.SHACL += self.extractSubgraph(shape_add, identifier_add)

    def extractSubgraph(self, shape: Graph, identifier, visited_nodes=None):
        # Extract the subgraph starting from the given identifier
        if visited_nodes is None:
            visited_nodes = set()
        subgraph = Graph()
        for s, p, o in shape.triples((identifier, None, None)):
            subgraph += shape.triples((s,p,o))
            if o not in visited_nodes:
                visited_nodes.add(o)
                subgraph += shape.triples((o, None, None))
                subgraph += self.extractSubgraph(shape, o, visited_nodes)
        return subgraph
    
    def STATS(self):
        # Calculate the statistics of the final shape
        classes = set()
        properties = set()
        for s, p, o in self.SHACL:
            if p == self.shaclNS.targetClass:
                classes.add(o)
            elif p == self.shaclNS.path or p == self.shaclNS.targetSubjectsOf or p == self.shaclNS.targetObjectsOf:
                properties.add(o)
        print("STATS: ")
        print("\t Number of classes: ", len(classes))
        print("\t Number of properties: ", len(properties))

    def writeShapeToFile(self):
        self.STATS()
        validation_shape_graph = Graph().parse("shacl-shacl.ttl", format="turtle")
        r = validate(self.SHACL, shacl_graph=validation_shape_graph, ont_graph=None,
                     inference='rdfs', abort_on_first=False, meta_shacl=False, debug=False)
        if not r[0]:
            print(r[2])
        self.SHACL.serialize(destination=self.output, format='turtle')
        print("Saved final file in ", self.output)