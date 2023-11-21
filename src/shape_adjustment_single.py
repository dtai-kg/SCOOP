# Shape adjustment script that can be used to individually adjust the shape derived from XSD based on RML
# Input: RML graph, XSD-driven SHACL graph
# Output: Adjusted SHACL graph

from rdflib import Graph, URIRef, Literal, Namespace, BNode
from rdflib.namespace import RDF, RDFS, XSD, OWL
from pyshacl import validate
from .utils import GrapDFS
import re
import os
import sys
import random
import time

class ShapeAdjustment:
    def __init__(self, source_type):
        self.shaclNS = Namespace('http://www.w3.org/ns/shacl#')
        self.rdfSyntax = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.rmlNS = Namespace('http://semweb.mmlab.be/ns/rml#')
        self.r2rmlNS = Namespace('http://www.w3.org/ns/r2rml#')
        self.QLNS = Namespace('http://semweb.mmlab.be/ns/ql#')
        self.FNMLNS = Namespace('http://semweb.mmlab.be/ns/fnml#')
        self.LOGICAL_SOURCE = self.rmlNS.logicalSource
        self.SOURCE = self.rmlNS.source
        self.REFERENCE_FORMULATION = self.rmlNS.referenceFormulation
        self.ITERATOR = self.rmlNS.iterator
        self.TEMPLATE = self.r2rmlNS.template
        self.REFERENCE = self.rmlNS.reference
        self.CLASS = self.r2rmlNS["class"]
        self.POM = self.r2rmlNS.predicateObjectMap
        self.PREDICATE = self.r2rmlNS.predicate
        self.PRED_MAP = self.r2rmlNS.predicateMap
        self.TRIPLES_MAP_CLASS = self.r2rmlNS.TriplesMap
        self.SUBJECT_MAP = self.r2rmlNS.subjectMap
        self.OBJECT_MAP = self.r2rmlNS.objectMap
        self.DATATYPE = self.r2rmlNS.datatype
        self.CONSTANT = self.r2rmlNS.constant
        self.OBJECT = self.r2rmlNS.object
        self.PARENTTM = self.rmlNS.parentTriplesMap

        #self.XPathFunction = ["string","codepoints-to-string","string-to-codepoints","codepoint-equal","compare","concat","string-join","substring","string-length","normalize-space","normalize-unicode","upper-case","lower-case","translate","escape-uri","contains","starts-with","ends-with","substring-before","substring-after","matches","replace","tokenize"]
        
        self.source_type = source_type
        self.adjusted_graph = Graph()
        self.adjusted_identifier = []
        self.shared_sm_identifier = {}
        self.shared_pom_identifier = {}
        self.random_number = [random.randint(1000, 9999) for i in range(3000)]
    
    def parseRML(self, rml_graph: Graph):
        """
        A function to parse the RML graph and return a list of dictionary of the triples maps 
        (path of subject map, predicate map, object map, logical source, and classes and properties)
        """
        self.rml_graph = rml_graph
        self.iterator = None
        self.findNS = []
        self.findPS = []
        self.adjusted_shape = []
        self.rml_parsed = {}
        for triples_map_identifier in self.rml_graph.subjects(RDF.type, self.TRIPLES_MAP_CLASS):
            self.rml_parsed[triples_map_identifier] = {}

            source_identifier = self.rml_graph.value(triples_map_identifier, self.LOGICAL_SOURCE)
            source, reference_formulation, iterator = self.getSource(source_identifier)
            # self.setSourceType(reference_formulation, iterator)
            if iterator == None:
                self.iterator = ""
            else:
                self.iterator = iterator
            self.rml_parsed[triples_map_identifier] = {'source': source, 'reference_formulation': reference_formulation, 'iterator': iterator}
            
            subject_map_identifier = self.rml_graph.value(triples_map_identifier, self.SUBJECT_MAP)
            path, classes,template_length, shared_key = self.getSubjectMap(subject_map_identifier)
            self.rml_parsed[triples_map_identifier]['sm'] = {'path': path, 'classes': classes, 'template_length': template_length, 'shared_key': shared_key}
            
            pom_list = []
            for pom_identifier in self.rml_graph.objects(triples_map_identifier, self.POM):
                pom_property = self.getPredicate(pom_identifier)
                pom_object_path, pom_object_datatype, pom_object_parent, pom_object_template_length, constant, termType = self.getObjectMap(pom_identifier)
                if pom_property == RDF.type:
                    self.rml_parsed[triples_map_identifier]['sm']['classes'].extend(pom_object_path)
                else:
                    pom_list.append({'property': pom_property, 'path': pom_object_path, 'datatype': pom_object_datatype, 'parent': pom_object_parent, 'template_length': pom_object_template_length, 'constant': constant, 'termType': termType})
            self.rml_parsed[triples_map_identifier]['pom'] = pom_list
        # print(self.rml_parsed)
        # print("\n")
        # sys.exit()
        # print(self.shape_path)
    def parseRawDataSchemaShape(self, initial_graph: Graph):
        self.initial_graph = initial_graph
        self.shape_path = {}
        getattr(self, f"parse_{self.source_type}", None)()

    def getSource(self, source_identifier):
        """
        A function to get the logical source of a triples map
        """
        source, reference_formulation, iterator = None, None, None
        for s, p, o in self.rml_graph:
            if s == source_identifier and p == self.SOURCE:
                source = re.sub(r'\[.*?\]', '', str(o))
            elif s == source_identifier and p == self.REFERENCE_FORMULATION:
                reference_formulation = o
            elif s == source_identifier and p == self.ITERATOR:
                iterator = re.sub(r'\[.*?\]', '', str(o))
        return source, reference_formulation, iterator

    # def setSourceType(self, reference_formulation, iterator):
    #     if reference_formulation == self.QLNS.CSV:
    #         self.source_type = 'csv'
    #     elif reference_formulation == self.QLNS.XPath:
    #         self.source_type = 'xml'
    #         self.iterator = iterator
    #     elif reference_formulation == self.QLNS.JSONPath:
    #         self.source_type = 'json'
    #         self.iterator = iterator

    def getSubjectMap(self, subject_map_identifier):
        """
        A function to get the subject map of a triples map
        """
        path, classes, template_length, shared_key = [], [], None, None
        for s, p, o in self.rml_graph:
            if s == subject_map_identifier and p == self.TEMPLATE:
                path.extend(getattr(self, f"parseTemplate_{self.source_type}", None)(o))
                template_length = 0
                for i in str(o).split("{"):
                    template_length+=len(i.split("}")[-1])
                shared_key = self.clean_shared_key(str(o))
            elif s == subject_map_identifier and p == self.REFERENCE:
                path.extend(getattr(self, f"parseReference_{self.source_type}", None)(o))
                shared_key = self.clean_shared_key(str(o))
            elif s == subject_map_identifier and p == self.CLASS:
                classes.append(o)
        return path, classes, template_length, shared_key

    def clean_shared_key(self, shared_key):
        # remove_list = ["parent::*/parent::", "parent::*/", "parent::",]
        shared_key = re.sub(r'parent::[^/]*\/', '', shared_key)
        shared_key = re.sub(r'{[^{]*?\[.*\]/', '{', shared_key)
        return shared_key

    def getPredicate(self, pom_identifier):
        """
        A function to get the predicate of a triples map
        """
        for s, p, o in self.rml_graph:
            if s == pom_identifier and p == self.PREDICATE:
                return o
            elif s == pom_identifier and p == self.CONSTANT:
                return o
            elif s == pom_identifier and p == self.PRED_MAP:
                o = self.getPredicate(o)
                return o

    def getObjectMap(self, pom_identifier, parent=False):
        """
        A function to get the object map of a triples map
        """
        path, datatype, parent, template_length, constant, termType = [], None, False, None, False, None
        for s, p, o in self.rml_graph:
            if s == pom_identifier and p == self.OBJECT:
                path.append(o)
            elif s == pom_identifier and p == self.OBJECT_MAP:
                path, datatype, parent, template_length, constant, termType = self.getObjectMap(o)
            elif s == pom_identifier and p == self.DATATYPE:
                datatype = o
            elif s == pom_identifier and p == self.r2rmlNS.termType:
                termType = self.shaclNS[str(o).split("#")[-1]]
            elif s == pom_identifier and p == self.TEMPLATE:
                path.extend(getattr(self, f"parseTemplate_{self.source_type}", None)(o))
                template_length = 0
                for i in str(o).split("{"):
                    template_length+=len(i.split("}")[-1])
                shared_key = str(o)
            elif s == pom_identifier and p == self.REFERENCE:
                path.extend(getattr(self, f"parseReference_{self.source_type}", None)(o))
                shared_key = str(o)
            elif s == pom_identifier and p == self.CONSTANT:
                path.append(o)
                constant = True
            elif s == pom_identifier and p == self.PARENTTM:
                path.append(o)
            elif s == pom_identifier and p == self.FNMLNS.functionValue:
                path = self.getFunctionValue(o)
                #path.append("skip_function")
                return path, datatype, parent, template_length, constant, termType
        return path, datatype, parent, template_length, constant, termType

    def getFunctionValue(self, function_identifier):
        """
        A function to get the function value of a triples map
        """
        path = []
        for s, p, o in self.rml_graph:
            if s == function_identifier and p == self.POM:
                path = self.getFunctionValue(o)
            elif s == function_identifier and p == self.OBJECT_MAP:
                path = self.getFunctionValue(o)
            elif s == function_identifier and p == self.REFERENCE:
                path.extend(getattr(self, f"parseReference_{self.source_type}", None)(o))
        return path
    
    def parseTemplate_csv(self, template):
        """
        A function to parse the template in a triples map and return path list
        """
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, template)
        matches = [self.iterator+"/" + i for i in matches]

        return [matches]

    def parseReference_csv(self, reference):
        """
        A function to parse the reference in a triples map and return path list
        """
        pass
    
    def parseTemplate_xml(self, template):
        """
        A function to parse the template in a triples map and return path list
        """
        self.XPathFunction = {"string":'string\((.*?)\)',
        "substring":'substring\((.*?)\,',
        "string-length":'string-length\((.*?)\)',
        "upper-case":'upper-case\((.*?)\)',
        "lower-case":'lower-case\((.*?)\)',
        "substring-before":'substring-before\((.*?)\,',
        "substring-after":'substring-after\((.*?)\,',
        "replace":'replace\((.*?)\,'}
        
        template = re.sub(r'\[.*?\]', '', template)
        matches = re.findall(r'\{([^}]+)\}', template)
        for i in range(len(matches)):
            for function in self.XPathFunction:
                if function in matches[i]:
                    m = re.search(self.XPathFunction[function], matches[i])
                    if m:
                        matches[i] = m.group(1)
        matches = [self.iterator+"/"+i.replace("@","") for i in matches]
  
        return [matches]

    def parseReference_xml(self, reference):
        """
        A function to parse the reference in a triples map and return path list
        """
        self.XPathFunction = {"string":'string\((.*?)\)',
        "substring":'substring\((.*?)\,',
        "string-length":'string-length\((.*?)\)',
        "upper-case":'upper-case\((.*?)\)',
        "lower-case":'lower-case\((.*?)\)',
        "substring-before":'substring-before\((.*?)\,',
        "substring-after":'substring-after\((.*?)\,',
        "replace":'replace\((.*?)\,'}

        for function in self.XPathFunction:
            if function in reference:
                m = re.search(self.XPathFunction[function], reference)
                if m:
                    reference = m.group(1)
        reference = re.sub(r'\[.*?\]', '', reference)
        return [[self.iterator+"/"+reference.replace("@","")]]

    def parseTemplate_json(self, template):
        """
        A function to parse the template in a triples map and return path list
        """
        pass

    def parseReference_json(self, reference):
        """
        A function to parse the reference in a triples map and return path list
        """
        pass
    
    def parse_xml(self):
        """
        A function to parse XSD to return the identifier of shape and corresponding XPath
        """
        complex_type_list = self.getComplexType()
        self.getShapePath(complex_type_list)
        
    def getComplexType(self):
        """
        A function to get the identifier of the shape that translated from complex type
        """
        complex_type_list = []
        for s, p, o in self.initial_graph.triples((None, self.shaclNS.node, None)):
            if len(str(o).split("http://example.com/NodeShape/")[-1].split("/")) == 1:
                complex_type_list.append(str(o).split("http://example.com/NodeShape/")[-1])
        return list(set(complex_type_list))

    def getShapePath(self, complex_type_list):
        gdfs = GrapDFS()

        for s, p, o in self.initial_graph.triples((None, self.shaclNS.property, None)):
            gdfs.add_edge(str(o), str(s))
        for s, p, o in self.initial_graph.triples((None, self.shaclNS.node, None)):
            if "http://example.com/NodeShape/None" != str(o):
                gdfs.add_edge(str(o), str(s))
        result = gdfs.find_paths()

        for _, node_paths in result.items():
            for path in node_paths:
                l = self.shape_path.get(path[0],[])
                l.append(path)
                self.shape_path[path[0]] = l

        for identifier in self.shape_path:  
            for p in range(len(self.shape_path[identifier])):
                url_list = self.shape_path[identifier][p]
                paths = []
                for i in range(len(url_list)):
                    url = url_list[i]
                    if url.split('/')[-1] not in complex_type_list:
                        if i != len(url_list)-1:
                            paths.append(url.split('/')[-1])
                        elif "NodeShape" in url:
                            paths.append(url.split('NodeShape/')[-1])
                        elif "PropertyShape" in url:
                            paths.append(url.split('PropertyShape/')[-1])
                paths = paths[::-1]
                # paths = [url.split('/')[-1] for url in url_list if url.split('/')[-1] not in complex_type_list][::-1]
                result = '/'.join(paths)
                # result = re.sub(r'([^/]+)/\1', r'\1', result)
                result = re.sub(r'(/[^/]+)/\1', r'\1', result)
                # Remove duplicate path
                path_parts = result.split('/')
                result = path_parts[0]
                for i in range(1,len(path_parts)):
                    part = path_parts[i]
                    if part != path_parts[i-1]:
                        result += '/' + part

                if result[0] != '/':
                    result = '/'+result
                self.shape_path[identifier][p] = result


    def getPath(self, identifier, complex_type_list):
        identifier = str(identifier)
        if "NodeShape" in identifier:
            p = identifier.split("http://example.com/NodeShape/")[-1].split("/")
            p = [i for i in p if i not in complex_type_list]
            return "/".join(p)
        elif "PropertyShape" in identifier:
            p = identifier.split("http://example.com/PropertyShape/")[-1].split("/")
            p = [i for i in p if i not in complex_type_list]
            return "/".join(p)
    
    def adjust_sm(self, sm_path, sm_classes, shared_key):
        """
        Adjust target declarations of shape
        """

        if shared_key in self.shared_sm_identifier:
            for shape_identifier in self.shared_sm_identifier[shared_key]:
                for sm_class in sm_classes:
                    self.initial_graph.add((URIRef(shape_identifier), self.shaclNS.targetClass, URIRef(sm_class)))
                self.findNS.append(URIRef(shape_identifier))
            return None

        # if sm_classes == []:
        #     return None

        temp_pop = str(self.random_number.pop())
        for path_list in sm_path:
            for path in path_list:
                for shape_identifier in self.shape_path:
                    if "PropertyShape" in shape_identifier:
                        continue
                    for initial_path in self.shape_path[shape_identifier]:
                        if initial_path == path or initial_path == self.iterator or path.endswith(initial_path) or ("parent:" in path and self.validatePath(path, initial_path)):
                            if URIRef(shape_identifier) in self.adjusted_shape:
                                #new_shape_identifier = shape_identifier + "/" + "/".join([i.split("/")[-1] for i in sm_classes])
                                new_shape_identifier = shape_identifier + "/" + "/".join([i.split("/")[-1] for i in sm_classes]) + temp_pop
                                self.updateShape(URIRef(shape_identifier), URIRef(new_shape_identifier))
                                shape_identifier = new_shape_identifier
                            
                            self.initial_graph.remove((URIRef(shape_identifier), self.shaclNS.targetClass, None))
                            self.findNode(URIRef(shape_identifier))
                            for sm_class in sm_classes:
                                self.initial_graph.add((URIRef(shape_identifier), self.shaclNS.targetClass, URIRef(sm_class)))
                            
                            l = self.shared_sm_identifier.get(shared_key,[])
                            l.append(shape_identifier)
                            self.shared_sm_identifier[shared_key] = l

                            self.findNS.append(URIRef(shape_identifier))
                            self.adjusted_shape.append(URIRef(shape_identifier))
        
        if self.findNS == []:
            shape_identifier = URIRef("http://example.com/NodeShape/" + "/".join([i.split("/")[-1] for i in sm_classes]))
            self.initial_graph.add((shape_identifier, RDF.type, self.shaclNS.NodeShape))
            for sm_class in sm_classes:
                self.initial_graph.add((shape_identifier, self.shaclNS.targetClass, URIRef(sm_class)))
            self.initial_graph.add((shape_identifier, self.shaclNS.nodeKind, self.shaclNS.IRI))

            l = self.shared_sm_identifier.get(shared_key,[])
            l.append(shape_identifier)
            self.shared_sm_identifier[shared_key] = l

            self.findNS.append(shape_identifier)
            self.adjusted_shape.append(shape_identifier)


    def updateShape(self, shape_identifier, new_shape_identifier):
        for s, p, o in self.initial_graph.triples((shape_identifier, None, None)):
            self.initial_graph.add((new_shape_identifier,p,o))
        for s, p, o in self.initial_graph.triples((None, None, shape_identifier)):
            self.initial_graph.add((s,p,new_shape_identifier))

    def updateSharedShape(self):
        pass

    def findNode(self, node):
        for s, p, o in self.initial_graph.triples((node, self.shaclNS.node, None)):
            self.adjusted_shape.append(o)
            self.initial_graph.remove((o, self.shaclNS.targetClass, None))
            self.initial_graph.remove((o, self.shaclNS.targetNode, None))
            self.initial_graph.remove((o, self.shaclNS.targetObjectsOf, None))
            self.initial_graph.remove((o, self.shaclNS.targetSubjectsOf, None))
            self.findNode(o)

    def adjust_pom(self, pom_list):
        if self.findNS == []:
            return None  # Comment it and next one if you want to add targetSubjectsOf to the shape which doesn't referenced by a node shape that has target declaration
        for pom in pom_list:
            for path_list in pom["path"]:
                if len(path_list) == 1:
                    path = path_list[0]
                    for shape_identifier in self.shape_path:
                        if "NodeShape" in shape_identifier:
                            continue 
                        for initial_path in self.shape_path[shape_identifier]:   
                            if (initial_path == path) or path.endswith(initial_path) or (pom["constant"] == True and initial_path == self.iterator) or ("parent:" in path and self.validatePath(path, initial_path)):
                                shape_identifier = URIRef(shape_identifier)
                                if shape_identifier in self.adjusted_shape:
                                    # new_shape_identifier = shape_identifier + "/" + pom["property"].split("/")[-1]
                                    new_shape_identifier = URIRef(str(shape_identifier) + "/" + pom["property"].split("/")[-1] + str(self.random_number.pop()))
                                    self.updateShape(shape_identifier, new_shape_identifier)
                                    shape_identifier = new_shape_identifier
                                self.adjusted_shape.append(shape_identifier)
                                self.initial_graph.remove((shape_identifier, self.shaclNS.path, None))
                                self.initial_graph.add((shape_identifier, self.shaclNS.path, pom["property"]))
                                if pom["datatype"] is not None:
                                    self.initial_graph.remove((shape_identifier, self.shaclNS.nodeKind, None))
                                    self.initial_graph.remove((shape_identifier, self.shaclNS.datatype, None))
                                    self.initial_graph.add((shape_identifier, self.shaclNS.datatype, pom["datatype"]))
                                if pom["termType"] is not None:
                                    self.initial_graph.remove((shape_identifier, self.shaclNS.nodeKind, None))
                                    self.initial_graph.add((shape_identifier, self.shaclNS.nodeKind, pom["termType"]))
                                if pom["template_length"] is not None:
                                    value = self.initial_graph.value(shape_identifier, self.shaclNS.minLength)
                                    if value is not None:
                                        self.initial_graph.remove((shape_identifier, self.shaclNS.minLength, value))
                                        self.initial_graph.add((shape_identifier, self.shaclNS.minLength, Literal(int(pom["template_length"])+int(value))))
                                    value = self.initial_graph.value(shape_identifier, self.shaclNS.maxLength)
                                    if value is not None:
                                        self.initial_graph.remove((shape_identifier, self.shaclNS.maxLength, value))
                                        self.initial_graph.add((shape_identifier, self.shaclNS.maxLength, Literal(int(pom["template_length"])+int(value))))
                                # if self.findNS == []:
                                #     self.initial_graph.add((shape_identifier, self.shaclNS.targetSubjectsOf, pom["property"]))
                                self.findPS.append(shape_identifier)
                                for subject in self.findNS:
                                    self.initial_graph.add((subject, self.shaclNS.property, shape_identifier))
 
                else:
                    constraints = {}
                    for path in path_list:
                        for shape_identifier_temp in self.shape_path:
                            if "NodeShape" in shape_identifier_temp:
                                continue
                            for initial_path in self.shape_path[shape_identifier_temp]:
                                if (initial_path == path) or path.endswith(initial_path) or (pom["constant"] == True and initial_path == self.iterator) or ("parent:" in path and self.validatePath(path, initial_path)):
                                #if initial_path == path or path.endswith(initial_path) or ("parent:" in path and self.validatePath(path, initial_path)):
                                    shape_identifier = shape_identifier_temp
                                    constraints = self.getConstraints(URIRef(shape_identifier_temp), constraints)
                    if constraints!={}:
                        # new_shape_identifier = shape_identifier + "/" + pom["property"].split("/")[-1]     
                        shape_identifier = shape_identifier + "/" + pom["property"].split("/")[-1] + str(self.random_number.pop())
                        self.adjusted_shape.append(URIRef(shape_identifier))
                        self.updateCombinationShape(URIRef(shape_identifier), pom["property"], constraints,pom["template_length"])
                        self.findPS.append(URIRef(shape_identifier))
            
            if self.findPS == []:
                # shape_identifier = URIRef("http://example.com/PropertyShape/" + pom["property"].split("/")[-1])
                shape_identifier = URIRef("http://example.com/PropertyShape/" + pom["property"].split("/")[-1] + str(self.random_number.pop()))
                
                self.initial_graph.add((shape_identifier, RDF.type, self.shaclNS.PropertyShape))
                self.initial_graph.add((shape_identifier, self.shaclNS.path, pom["property"]))
                for subject in self.findNS:
                    self.initial_graph.add((subject, self.shaclNS.property, shape_identifier))
                else:
                    self.initial_graph.add((shape_identifier, self.shaclNS.targetObjectsOf, pom["property"]))
                if pom["datatype"] is not None:
                    self.initial_graph.add((shape_identifier, self.shaclNS.datatype, pom["datatype"]))
                if pom["termType"] is not None:
                    self.initial_graph.add((shape_identifier, self.shaclNS.nodeKind, pom["termType"]))
                    
                self.findPS.append(shape_identifier)
                self.adjusted_shape.append(shape_identifier)

            self.findPS = []

    def validatePath(self, path_target, path):
        result = path_target.split("parent::")
        final_result = []
        for item in result:
            final_result.extend(item.split("*"))
        final_result = [i for i in final_result if i!=""]
        if path.endswith(final_result[-1]):
            for p in final_result[:-1]:
                if p not in path:
                    return False
            return True
        else:
            return False
    
    def generate_regex(self, paths):
        regex_pattern = ".*".join([re.escape(path) for path in paths])
        return ".*" + regex_pattern + "$"

    def getConstraints(self, shape_identifier, constraints):
        for s, p, o in self.initial_graph.triples((shape_identifier, None, None)):
            if p != RDF.type:
                l = constraints.get(p,[])
                l.append(o)
                constraints[p] = l
        return constraints

    def updateCombinationShape(self, shape_identifier, property, constraints, template_length):
        self.initial_graph.add((shape_identifier, RDF.type, self.shaclNS.PropertyShape))
        self.initial_graph.add((shape_identifier, self.shaclNS.nodeKind, self.shaclNS.IRI))
        self.initial_graph.add((shape_identifier, self.shaclNS.path, property))

        for subject in self.findNS:
            self.initial_graph.add((subject, self.shaclNS.property, shape_identifier))
        else:
            self.initial_graph.add((shape_identifier, self.shaclNS.targetObjectsOf, property))

        for constraint, constraint_value in constraints.items():
            if constraint == self.shaclNS.minCount or constraint == self.shaclNS.maxCount:
                current_number = 1
                for value in constraint_value:
                    current_number*=int(value)
                self.initial_graph.add((shape_identifier, constraint, Literal(current_number)))
            elif constraint == self.shaclNS.minLength or constraint == self.shaclNS.maxLength:
                current_number = template_length
                for value in constraint_value:
                    current_number+=int(value)
                self.initial_graph.add((shape_identifier, constraint, Literal(current_number)))

    def adjust_parentTM(self, parentTM):
        pass                        
    
    def clear_graph(self):
        identifier_to_remove = []
        for s,p,o in self.initial_graph:
            if p == RDF.type and (o == self.shaclNS.NodeShape or o == self.shaclNS.PropertyShape):
                if s not in self.adjusted_shape:
                    identifier_to_remove.append(s)
            if s == URIRef("http://example.com/NodeShape/None") or o == URIRef("http://example.com/NodeShape/None"):
                self.initial_graph.remove((s,p,o))
        self.remove_graph(identifier_to_remove)

    def remove_graph(self, old_subjects):
        for s,p,o in self.initial_graph:
            if s in old_subjects:
                self.initial_graph.remove((s,p,o))
                if isinstance(o,BNode):
                    self.remove_graph([o])
            elif o in old_subjects:
                self.initial_graph.remove((s,p,o))

    def reassign_identifier(self):
        current_adjusted_identifier = []    
        for s, p, o in self.initial_graph:
            if p == RDF.type and (o == self.shaclNS.NodeShape or o == self.shaclNS.PropertyShape):
                if s not in self.adjusted_identifier:
                    current_adjusted_identifier.append(s)
                else:
                    new_shape_identifier = URIRef(str(s)+str(self.random_number.pop()))
                    current_adjusted_identifier.append(new_shape_identifier)
                    for s2, p2, o2 in self.initial_graph:
                        if s2 == s:
                            self.initial_graph.remove((s2,p2,o2))
                            self.initial_graph.add((new_shape_identifier,p2,o2))
                        elif o2 == s:
                            self.initial_graph.remove((s2,p2,o2))
                            self.initial_graph.add((s2,p2,new_shape_identifier))
        self.adjusted_identifier.extend(current_adjusted_identifier)

    def double_check(self):
        double_check_list = [self.shaclNS.datatype, self.shaclNS["in"], self.shaclNS.languageIn, self.shaclNS.minCount, self.shaclNS.maxCount, self.shaclNS.minLength, self.shaclNS.maxLength, self.shaclNS.maxExclusive, self.shaclNS.minExclusive, self.shaclNS.maxInclusive, self.shaclNS.minInclusive, self.shaclNS.pattern, self.shaclNS.uniqueLang]
        for identifier in self.adjusted_identifier:
            if "NodeShape" in identifier:
                for s, p, o in self.adjusted_graph.triples((identifier, None, None)):
                    if p in double_check_list:
                        self.adjusted_graph.remove((s,p,o))

    def adjust(self, initial_graph):
        self.initial_graph = initial_graph 
        for triples_map_identifier in self.rml_parsed:
            self.adjust_sm(self.rml_parsed[triples_map_identifier]["sm"]["path"], self.rml_parsed[triples_map_identifier]["sm"]["classes"], self.rml_parsed[triples_map_identifier]["sm"]["shared_key"])
            self.adjust_pom(self.rml_parsed[triples_map_identifier]["pom"])
            self.findNS = []
        
        self.clear_graph()
        self.reassign_identifier()
        self.adjusted_graph+=self.initial_graph

    def writeShapeToFile(self, output_file):
        self.double_check()

        validation_shape_graph = Graph().parse("shacl-shacl.ttl", format="turtle")
        r = validate(self.adjusted_graph, shacl_graph=validation_shape_graph, ont_graph=None,
                     inference='rdfs', abort_on_first=False, meta_shacl=False, debug=False)
        if not r[0]:
            print(r[2])
        else:
            print("Saved to adjusted SHACL shapes to file", output_file)
        self.adjusted_graph.serialize(destination=output_file, format='turtle')

if __name__ == '__main__':

    # g_rml = Graph().parse('usecases/RINF/mappings/RINF-etcs-levels_rml.ttl', format='ttl')
    # g_rml2 = Graph().parse('usecases/RINF/mappings/RINF-load-capability_rml.ttl', format='ttl')
    # g_rml2 = Graph().parse('usecases/RINF/mappings/RINF-load-capability_rml.ttl', format='ttl')
    
    start_time = time.time()
    g_xsd = Graph().parse('adjustment_test/RINF-metadata.xsd.shape.ttl')
    files = []
    # rml = "usecases/RINF/mappings/"
    # files.extend([os.path.join(rml, f) for f in os.listdir(rml) if f.endswith('.ttl')])
    files = ["usecases/RINF/mappings/_RINF-operational-points_rml.ttl"]
    sa = ShapeAdjustment("xml")
    sa.parseRawDataSchemaShape(g_xsd)
    for i in range(len(files)):

        print("Start adjusting shape ", files[i])
        g_rml = Graph().parse(files[i], format='ttl')
        sa.parseRML(g_rml)
        sa.adjust(Graph()+g_xsd)
    sa.writeShapeToFile("test.ttl")
    end_time = time.time()
    print('Shape adjustment took %s seconds', end_time - start_time)



    # sa.parseRML(g_rml)
    # sa.adjust(Graph()+g_xsd)
    # sa.parseRML(g_rml2)
    # sa.adjust(Graph()+g_xsd)
    # sa.writeShapeToFile("adjustment_test/era_adjusted_shacl.ttl")
    # g_rml = Graph().parse('adjustment_test/rml.ttl', format='ttl')
    # g_xsd = Graph().parse('adjustment_test/xsd.shape.ttl')
    # sa = ShapeAdjustment("xml")
    # sa.parseRawDataSchemaShape(g_xsd)
    # sa.parseRML(g_rml)
    # sa.adjust(Graph()+g_xsd)
    # sa.writeShapeToFile("adjustment_test/test.lenth.ttl")

    # g_rml = Graph().parse('usecases/RINF/mappings/RINF-contact-line-systems_rml.ttl', format='ttl')
    # g_xsd = Graph().parse('adjustment_test/RINF-metadata.xsd.shape.ttl')

    # sa = ShapeAdjustment("xml")
    # sa.parseRawDataSchemaShape(g_xsd)
    # sa.parseRML(g_rml)
    # sa.adjust(Graph()+g_xsd)
    # sa.writeShapeToFile("test.ttl")