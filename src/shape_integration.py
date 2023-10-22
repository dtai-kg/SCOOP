import os
from pathlib import Path
from typing import List, Dict
from rdflib import Graph, Namespace, URIRef, Literal
import pprint


class shapeIntegration:
    def __init__(self, shapes: List):
        self.shaclNS = Namespace('http://www.w3.org/ns/shacl#')
        self.rdfSyntax = Namespace(
            'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.targetDeclarationNS = [self.shaclNS.targetClass, self.shaclNS.targetNode, self.shaclNS.targetSubjectsOf, self.shaclNS.targetObjectsOf]
        self.propertyPathNS = [self.shaclNS.path]
        self.shapes = shapes
        self.SHACL = Graph()
    
    def integration(self):
        for shape_add in self.shapes:
            target_current = self.getTargetDeclaration(self.SHACL)
            target_add = self.getTargetDeclaration(shape_add)

            if len(target_current) == 0:
                self.SHACL = shape_add
                continue

            common_targets = set(target_current.keys()).intersection(set(target_add.keys()))
            differ_targets = set(target_add.keys()).difference(set(target_current.keys()))
            # print("common_targets", common_targets)
            # print("differ_targets", differ_targets)

            for target, target_value in common_targets:
                identifiers_current =  list(target_current[(target, target_value)].keys())
                identifiers_add =  list(target_add[(target, target_value)].keys())
                
                for identifier_current in identifiers_current:
                    constraints_current = self.getConstraints(self.SHACL, identifier_current)
                    path_current = target_current[(target, target_value)][identifier_current]
                    
                    for identifier_add in identifiers_add:
                        constraints_add = self.getConstraints(shape_add, identifier_add)
                        # Add constraints in the shape that has target declaration
                        for constraint_add, constraint_add_value in constraints_add.items():
                            if constraint_add_value == constraints_current.get(constraint_add, None):
                                continue
                            else:
                                self.addConstraint(identifier_current, constraints_current, constraint_add, constraint_add_value)
                        
                        path_add = target_add[(target, target_value)][identifier_add]
                        common_paths = set(path_current.keys()).intersection(set(path_add.keys()))
                        differ_paths = set(path_add.keys()).difference(set(path_current.keys()))
                        # print("common_paths", common_paths)
                        # print("differ_paths", differ_paths)

                        for path, path_value in common_paths:

                            identifiers_path_current =  path_current[(path, path_value)]
                            identifiers_path_add =  path_add[(path, path_value)]

                            for identifier_path_current in identifiers_path_current:
                                constraints_current = self.getConstraints(self.SHACL, identifier_path_current)

                                for identifier_path_add in identifiers_path_add:
                                    constraints_add = self.getConstraints(shape_add, identifier_path_add)
                                    # Add constraints in the shape that has property path
                                    for constraint_add, constraint_add_value in constraints_add.items():
                                        if constraint_add_value == constraints_current.get(constraint_add, None):
                                            continue
                                        else:
                                            self.addConstraint(identifier_path_current, constraints_current, constraint_add, constraint_add_value)
                                            
            
            for target, target_value in differ_targets:
                pass
            
            self.writeShapeToFile("test2.ttl")

    def getTargetDeclaration(self, shape: Graph):
        targetDict = {}
        for identifier, p, o in shape:
            if p in self.targetDeclarationNS:
                l = targetDict.get((p,o),{})
                l[identifier] = self.getPropertyPath(l.get(identifier,{}),shape,identifier)
                targetDict[(p,o)] = l
        return targetDict

    def getPropertyPath(self, propertyPaths: Dict, shape: Graph, identifier):
        for s, p, o in shape:
            if s == identifier:
                if p in self.propertyPathNS:
                    l = propertyPaths.get((p,o),[])
                    l.append(s)
                    propertyPaths[(p,o)] = l
                elif p == self.shaclNS["property"]:
                    propertyPaths = self.getPropertyPath(propertyPaths, shape, o)
                elif p == self.shaclNS.node:
                    propertyPaths = self.getPropertyPath(propertyPaths, shape, o)
        return propertyPaths

    def getConstraints(self, shape: Graph, identifier):
        constraints = {}
        for s, p, o in shape:
            if s == identifier: 
                if (p not in [self.shaclNS.node, self.rdfSyntax.type]) and (p not in self.targetDeclarationNS) and (p not in self.propertyPathNS):
                    constraints[p] = o
        return constraints

    def addConstraint(self, identifier_path_current, constraints_current, constraint_add, constraint_add_value):
        if self.conflictChecking(constraints_current, constraint_add, constraint_add_value):
            self.SHACL.add((identifier_path_current, constraint_add, constraint_add_value))

    def conflictChecking(self, constraints_current, constraint_add, constraint_add_value):
        return True

    def writeShapeToFile(self, file_name, shape_dir="shapes/"):

        parent_folder = os.path.dirname(file_name)
        Path(f"%s%s" % (shape_dir, parent_folder)).mkdir(parents=True, exist_ok=True)

        filenNameShape = "%s%s" % (shape_dir, file_name)
        self.SHACL.serialize(destination=filenNameShape, format='turtle')

        return filenNameShape