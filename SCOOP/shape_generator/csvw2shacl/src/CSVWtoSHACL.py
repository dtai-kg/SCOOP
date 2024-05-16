import rdflib
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from pyshacl import validate
import argparse
import re
import os
from urllib.parse import quote
from .utils import json_load
from .utils import merge_property_shapes, delete_triples
from .utils import extract_paths, serializeTemplate
from .constraints import transConstraints, addDefaultConstriants
from .error_log import *
# from .logger import create_logger

class CSVWtoSHACL:
    def __init__(self):
        """

        """
        self.shaclNS = Namespace('http://www.w3.org/ns/shacl#')
        self.csvw = Namespace('http://www.w3.org/ns/csvw#')
        self.rdf = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.rdfs = Namespace('http://www.w3.org/2000/01/rdf-schema#')
        self.xsd = Namespace('http://www.w3.org/2001/XMLSchema#')
        self.vocab = json_load(os.path.join(os.path.dirname(__file__),"vocabulary/default_vocabulary_prefixes.json"))
        self.datatype = json_load(os.path.join(os.path.dirname(__file__),"vocabulary/xmlschema11_2.json"))
        self.ex = Namespace('http://example.com/')
        self.SHACL = Graph()
        self.SHACL.bind('sh', self.shaclNS)
        self.SHACL.bind('xsd', self.xsd)
        self.SHACL.bind('rdf', self.rdf)
        self.SHACL.bind('rdfs', self.rdfs)
        self.SHACL.bind('csvw', self.csvw)
        self.CSVW = {}
        self.virtualShapes = []
        self.aboutUrlShapes = {}

    def translate(self):

        if self.CSVW.get("tableSchema"):
            id_error_check(self.CSVW, self.logger)
            self.translateTableSchema(self.CSVW)

        elif self.CSVW.get("tables"):
            id_error_check(self.CSVW, self.logger)
            if not isinstance(self.CSVW["tables"], list):
                tablesarray_error(self.logger)
                return None
            for table in self.CSVW["tables"]:
                if table.get("suppressOutput") == True:
                    continue
                tableSchema = table.get("tableSchema")
                if isinstance(tableSchema, str):
                    tableSchema_path = os.path.join(self.folder_path, tableSchema)
                    table["tableSchema"]=json_load(tableSchema_path)
                    id_error_check(tableSchema, self.logger)
                    self.translateTableSchema(table)
                elif tableSchema:
                    id_error_check(tableSchema, self.logger)      
                    self.translateTableSchema(table)
        else:
            empty_error(self.logger)
        self.SHACL = addDefaultConstriants(self.SHACL,self.virtualShapes)

    def translateTableSchema(self, table):
        # Create a node shape for the table
        # TODO Check Node Shape Identifier and Property Shape Identifier Generation Rule
        url_valid = url_error_check(table, self.logger)
        if url_valid == False:
            self.NS = Namespace("undefined#")
            self.SHACL.bind('file', self.NS)
        else:
            self.create_default_namespace(table.get("url",""))
                    
        if table["tableSchema"].get("aboutUrl"):
            about_string = table["tableSchema"].get("aboutUrl")
            if about_string not in self.aboutUrlShapes:
                self.aboutUrlShapes[about_string] = self.create_namespace(about_string,"ns")
                self.SHACL.add((self.aboutUrlShapes[about_string], RDF.type, self.shaclNS.NodeShape))
            nsSubject = self.aboutUrlShapes[about_string]
            self.translateSPARQLTarget(nsSubject, about_string)
        else:
            if url_valid == False:
                nsSubject = self.ex[str(self.NS["/NodeShape"])]
            else:
                nsSubject = self.create_namespace(table.get("url",""), "ns")
            self.SHACL.add((nsSubject, self.shaclNS["targetObjectsOf"], self.csvw["describes"]))

        self.SHACL.add((nsSubject, RDF.type, self.shaclNS.NodeShape))
        if table["tableSchema"].get("columns"): 
            for column in table['tableSchema']['columns']:
                self.translateColumn(column, nsSubject)
            # translate foreignKeys
            if table["tableSchema"].get("foreignKeys"):
                for key in table["tableSchema"].get("foreignKeys"):
                    psSubject = self.create_namespace(key.get("columnReference"),"ps")
                    if key.get("reference").get("resource"):
                        nsSubject = self.create_namespace(key.get("reference").get("resource"),"ns")
                    else:
                        nsSubject = self.create_namespace(key.get("reference").get("schemaReference"),"ns")
                    self.SHACL.add((psSubject, self.shaclNS["node"], nsSubject))
            for key, value in table["tableSchema"].items():
                if ":name" in key or ":description" in key: 
                    self.SHACL.add((nsSubject, self.string_to_namespace(key), Literal(str(value))))

    def translateColumn(self, column, nsSubject):
        id_error_check(column, self.logger)

        if column.get("suppressOutput") == True:
            return None

        psSubject = None
        if column.get("virtual") == True:
            if column.get("propertyUrl") =='rdf:type':
                obj = URIRef(self.string_to_namespace(column["valueUrl"]))
                if column.get("aboutUrl") is None:
                    # Add targetClass and class to the node shape
                    self.SHACL.add((nsSubject, self.shaclNS["class"], obj))
                    self.SHACL.add((nsSubject, self.shaclNS["targetClass"], obj))
                    self.virtualShapes.append(nsSubject)
                else:        
                    # Add new node shape
                    about_string = column.get("aboutUrl")
                    if about_string not in self.aboutUrlShapes:
                        self.aboutUrlShapes[about_string] = self.create_namespace(about_string,"ns")
                        self.SHACL.add((self.aboutUrlShapes[about_string], RDF.type, self.shaclNS.NodeShape))
                    new_nsSubject = self.aboutUrlShapes[about_string]
                    # new_node_shape_subject = self.create_namespace(self.extract_paths(column.get("aboutUrl")),"ns")
                    self.SHACL.add((new_nsSubject , RDF.type, self.shaclNS.NodeShape))
                    self.SHACL.add((new_nsSubject, self.shaclNS["targetClass"], obj))
                    self.virtualShapes.append(new_nsSubject)
            else:
                # Add new property shape and link current property shape to another node shape
                v = column.get("propertyUrl", extract_paths(column.get("valueUrl")))
                if v is None:
                    # v = column.get("name", column.get("titles"))
                    v = column.get("titles")
                psSubject = self.create_namespace(v,"ps")
                if column.get("valueUrl") in self.aboutUrlShapes:
                    self.SHACL.add((psSubject, self.shaclNS["node"], self.aboutUrlShapes[column.get("valueUrl")]))

                if column.get("aboutUrl") is not None:
                    self.virtualShapes.append(psSubject)
                    about_string = column.get("aboutUrl")
                    if about_string not in self.aboutUrlShapes:
                        self.aboutUrlShapes[about_string] = self.create_namespace(about_string,"ns")
                        self.SHACL.add((self.aboutUrlShapes[about_string], RDF.type, self.shaclNS.NodeShape))
                    new_nsSubject = self.aboutUrlShapes[about_string]

                    self.SHACL.add((new_nsSubject, self.shaclNS["property"], psSubject))
                    obj = self.string_to_namespace(column.get("propertyUrl"))
                    if obj is not None:
                        self.SHACL.add((psSubject, self.shaclNS["path"], obj))
                    else:
                        self.SHACL = delete_triples(self.SHACL, psSubject)
                        return None

                    # self.SHACL.add((psSubject, self.shaclNS["node"], self.create_namespace(column.get("valueUrl"),"ns")))
                    self.SHACL.add((psSubject, RDF.type, self.shaclNS.PropertyShape))
                    for k,v in column.items():
                        self.SHACL = transConstraints(self.SHACL,psSubject,k,v,self.logger)
                else:
                    self.SHACL.add((nsSubject, self.shaclNS["property"], psSubject))
                    self.SHACL.add((psSubject, RDF.type, self.shaclNS.PropertyShape))
                    if column.get("propertyUrl"):
                        # Add path to property shape
                        obj = self.string_to_namespace(column.get("propertyUrl"))
                        if obj is not None:
                            self.SHACL.add((psSubject, self.shaclNS["path"], obj))
                        else:
                            self.SHACL = delete_triples(self.SHACL, psSubject)
                            return None
                    else:
                        # Add path with default namespace and title to property shape
                        # obj = column.get("name", column.get("titles"))
                        obj = column.get("titles")
                        if isinstance(obj, str):
                            self.SHACL.add((psSubject, self.shaclNS["path"], self.create_namespace(obj)))
                        else:
                            #self.logger.warning(f"Column name or titles is not a string: {obj} in csvw file {self.csvw_file}")
                            self.logger.warning(f"Column name or titles is not a string: {obj} in csvw file {self.csvw_file}")
                            return None
                    self.SHACL.add((psSubject, RDF.type, self.shaclNS.PropertyShape))
                    # if column.get("aboutUrl"):
                    #     # Link property shape to aboutUrl's node shape
                    #     about_string = column.get("aboutUrl")
                    #     nsSubject = self.create_namespace(about_string,"ns")
                    #     self.SHACL.add((nsSubject, self.shaclNS["property"], psSubject))
                    #     template_strings = serializeTemplate(about_string)
                    #     self.SHACL.add((nsSubject, self.shaclNS["pattern"], template_strings))
                    # else:
                    #     # Link property shape to current node shape
                    #     self.SHACL.add((nsSubject, self.shaclNS["property"], psSubject))
                    for k,v in column.items():
                        self.SHACL = transConstraints(self.SHACL,psSubject,k,v,self.logger)
        else:
            # Add new property shape 
            # obj = column.get("name", column.get("titles", column.get("propertyUrl")))
            obj = column.get("titles")
            if isinstance(obj, str):
                psSubject = self.create_namespace(obj,"ps")
            else:
                #self.logger.warning(f"Column name or titles or propertyUrl is not a string: {obj} in csvw file {self.csvw_file}")
                self.logger.warning(f"Column name or titles or propertyUrl is not a string: {obj} in csvw file {self.csvw_file}")
                return None

            self.SHACL.add((psSubject, RDF.type, self.shaclNS.PropertyShape))
            if column.get("propertyUrl"):
                # Add path to property shape
                obj = self.string_to_namespace(column.get("propertyUrl"))
                if obj is not None:
                    self.SHACL.add((psSubject, self.shaclNS["path"], obj))
                else:
                    self.SHACL = delete_triples(self.SHACL, psSubject)
                    return None
            else:
                # Add path with default namespace and title to property shape
                # obj = column.get("name", column.get("titles"))
                obj = column.get("titles")
                if isinstance(obj, str):
                    self.SHACL.add((psSubject, self.shaclNS["path"], self.create_namespace(obj)))
                else:
                    #self.logger.warning(f"Column name or titles is not a string: {obj} in csvw file {self.csvw_file}")
                    self.logger.warning(f"Column name or titles is not a string: {obj} in csvw file {self.csvw_file}")
                    return None
            self.SHACL.add((psSubject, RDF.type, self.shaclNS.PropertyShape))

            if column.get("aboutUrl"):
                # Link property shape to aboutUrl's node shape
                about_string = column.get("aboutUrl")
                if about_string not in self.aboutUrlShapes:
                    self.aboutUrlShapes[about_string] = self.create_namespace(about_string,"ns")
                    self.SHACL.add((self.aboutUrlShapes[about_string], RDF.type, self.shaclNS.NodeShape))
                new_nsSubject = self.aboutUrlShapes[about_string]

                self.SHACL.add((new_nsSubject, self.shaclNS["property"], psSubject))
                template_strings = serializeTemplate(about_string)
                self.SHACL.add((new_nsSubject, self.shaclNS["pattern"], template_strings))
            else:
                # Link property shape to current node shape
                self.SHACL.add((nsSubject, self.shaclNS["property"], psSubject))

            for k,v in column.items():
                self.SHACL = transConstraints(self.SHACL,psSubject,k,v,self.logger)

        if psSubject:
            for key, value in column.items():
                if ":name" in key or ":description" in key: 
                    self.SHACL.add((psSubject, self.string_to_namespace(key), Literal(str(value))))

    # def transConstraints(self,sub,k,v):
    #     base = None
    #     if k == "name":
    #         self.SHACL.add((sub, self.shaclNS["name"], Literal(v)))
    #     elif k == "datatype":
    #         if isinstance(v, str):
    #             self.SHACL.add((sub, self.shaclNS["datatype"], self.transDatatype(v)))
    #         else:
    #             if v.get("base"):
    #                 base = self.transDatatype(v.get("base"))
    #                 self.SHACL.add((sub, self.shaclNS["datatype"], base))
    #             if v.get("minimum"):
    #                 try:
    #                     self.SHACL.add((sub, self.shaclNS["minInclusive"], Literal(int(v.get("minimum")))))
    #                 except:
    #                     self.SHACL.add((sub, self.shaclNS["minInclusive"], Literal(v.get("minimum"))))
    #             if v.get("maximum"):
    #                 try:
    #                     self.SHACL.add((sub, self.shaclNS["maxInclusive"], Literal(int(v.get("maximum")))))
    #                 except:
    #                     self.SHACL.add((sub, self.shaclNS["maxInclusive"], Literal(v.get("maximum"))))
    #             if v.get("minInclusive"):
    #                 try:
    #                     self.SHACL.add((sub, self.shaclNS["minInclusive"], Literal(int(v.get("minInclusive")))))
    #                 except:
    #                     self.SHACL.add((sub, self.shaclNS["minInclusive"], Literal(v.get("minInclusive"))))
    #             if v.get("maxInclusive"):
    #                 try:
    #                     self.SHACL.add((sub, self.shaclNS["maxInclusive"], Literal(int(v.get("maxInclusive")))))
    #                 except:
    #                     self.SHACL.add((sub, self.shaclNS["maxInclusive"], Literal(v.get("maxInclusive"))))
    #             if v.get("minExclusive"):
    #                 try:
    #                     self.SHACL.add((sub, self.shaclNS["minExclusive"], Literal(int(v.get("minExclusive")))))
    #                 except:
    #                     self.SHACL.add((sub, self.shaclNS["minExclusive"], Literal(v.get("minExclusive"))))
    #             if v.get("maxExclusive"):
    #                 try:
    #                     self.SHACL.add((sub, self.shaclNS["maxExclusive"], Literal(int(v.get("maxExclusive")))))
    #                 except:
    #                     self.SHACL.add((sub, self.shaclNS["maxExclusive"], Literal(v.get("maxExclusive"))))
    #             if v.get("length"):
    #                 self.SHACL.add((sub, self.shaclNS["maxLength"], Literal(int(v.get("length")))))
    #                 self.SHACL.add((sub, self.shaclNS["minLength"], Literal(int(v.get("length")))))
    #             if v.get("minLength"):
    #                 self.SHACL.add((sub, self.shaclNS["minLength"], Literal(int(v.get("minLength")))))
    #             if v.get("maxLength"):
    #                 self.SHACL.add((sub, self.shaclNS["maxLength"], Literal(int(v.get("maxLength")))))
    #             # if v.get("format"):
    #             # TODO Check format translation
    #             #     self.SHACL.add((sub, self.shaclNS["pattern"], Literal(v.get("format"))))
    #     elif k == "required":
    #         if v == True:
    #             self.SHACL.add((sub, self.shaclNS["minCount"], Literal(1)))
    #     elif k == "default":
    #         self.SHACL.add((sub, self.shaclNS["defaultValue"], Literal(v)))
    #     elif k == "lang":
    #         bn = BNode()
    #         self.SHACL.add((sub, self.shaclNS["languageIn"], bn))
    #         self.SHACL.add((bn, RDF.first, Literal(v)))
    #         self.SHACL.add((bn, RDF.rest, RDF.nil))

    # def transDatatype(self,datatype):
    #     #translate from complete built-in datatypes, based on [xmlschema11-2]
    #     if datatype in self.datatype:
    #         return URIRef(self.datatype[datatype])
    #     else:
    #         raise ValueError(f"Datatype '{datatype}' not found in default datatypes.")


    # def addDefaultConstriants(self):
    #     # Add default datatype string to each property shape who doesn't have datatype
    #     for s,p,o in self.SHACL.triples((None, self.shaclNS["path"], None)):
    #         if (s not in self.virtualShapes) and (not (s, self.shaclNS["datatype"], None) in self.SHACL):
    #             self.SHACL.add((s, self.shaclNS["datatype"], self.xsd.string))


    # def delete_triples(self, subject):
    #     for s,p,o in self.SHACL:
    #         if s == subject:
    #             self.SHACL.remove((s,p,o))
    #         elif o == subject:
    #             self.SHACL.remove((s,p,o))


    def combineSamePropertyShape(self):
        pass

    
    def create_namespace(self, s, shape_type=None):
        if isinstance(s, list):
            # If titles object is list
            # s = "/".join(s)
            s = "_".join(s)
        if shape_type == "ns":
            # return self.NS[f'NodeShape/{quote(s, safe='/:#')}']
            if re.match(r'https?://', str(s)) or re.match(r'http?://', str(s)):
                return URIRef(quote(s, safe='/:#')+"/NodeShape")
            else:
                # return self.ex[quote(s, safe='/:#')+"/NodeShape"]
                return self.ex[str(self.NS[quote(s, safe='/:#')+"/NodeShape"])]
        elif shape_type == "ps":
            # return self.NS[f'PropertyShape/{quote(s, safe='/:#')}']
            if re.match(r'https?://', str(s)) or re.match(r'http?://', str(s)):
                #TODO change URL tempalte to ex+property path+PropertyShape+csv path
                return URIRef(quote(s, safe='/:#')+"/PropertyShape")
            # elif ":" in s:
            #     return self.NS[quote(s, safe='/:#').split(":")[-1]+"/PropertyShape"]
            else:
                # return self.ex["PropertyShape/"+quote(s, safe='/:#')]
                return self.ex[str(self.NS["PropertyShape/"+quote(s, safe='/:#')])]
        else:
            if re.match(r'https?://', str(s)) or re.match(r'http?://', str(s)):
                return URIRef(quote(s, safe='/:#'))
            else:
                return self.NS[quote(s, safe='/:#')]
    
    def string_to_namespace(self, s):
        if (re.match(r'https?://', s) or re.match(r'http?://', s)) and "{" not in s:
            return URIRef(s)
        elif ":" in s and "{" not in s:
            prefix, localname = s.split(":")
            if prefix in self.vocab:
                # return getattr(self, prefix)[localname]
                URL =  Namespace(self.vocab[prefix])
                self.SHACL.bind(prefix, URL)
                return URL[localname]
            else:
                raise ValueError(f"Prefix '{prefix}' not found in default vocabulary prefixes.")
        else:
            #TODO SPARQL to find property path: test039
            return None

    def create_default_namespace(self, file_url):
        if re.match(r'https?://', file_url) or re.match(r'http?://', file_url):
            self.NS = Namespace(file_url+"#")
        else:
            # got the relative path of the file
            # file_relative_path = "file:" + os.path.join(self.csv_file_location, quote(file_url, safe='/:#')).replace("\\", "/")
            file_relative_path = os.path.join(self.csv_file_location, quote(file_url, safe='/:#')).replace("\\", "/")
            self.NS = Namespace(file_relative_path+"#")
            self.SHACL.bind('file', self.NS)

    # def extract_paths(self, url):
    #     if "{" in url:
    #         pattern = r"\{([^}]*)\}"
    #         matches = re.findall(pattern, url)
    #         return matches
    #     else:
    #         return url

    def translateSPARQLTarget(self, subject, subject_template):

        pattern = r'\{[^}]+\}'
        subject_template = re.sub(pattern, r'.+', subject_template)

        sparqlTargetTemplate = """ SELECT ?this WHERE {
                    ?this ?p ?o .
                    FILTER REGEX(STR(?this), '"""+ subject_template +"""') .} """ 

        bn = BNode()
        self.SHACL.add((subject, self.shaclNS["sparql"], bn))
        self.SHACL.add((bn, RDF.type, self.shaclNS["SPARQLTarget"]))

        declareBn = BNode()
        self.SHACL.add((bn, self.shaclNS["declare"], declareBn))
        self.SHACL.add((declareBn, self.shaclNS["prefix"], Literal("file")))
        self.SHACL.add((declareBn, self.shaclNS["namespace"], URIRef(self.NS)))

        self.SHACL.add((bn, self.shaclNS["select"], Literal(sparqlTargetTemplate)))

    
    def writeShapeToFile(self, file_name):
        self.SHACL.serialize(destination=file_name, format='turtle')

    def evaluate_file(self, csvw_file, csv_file_location, output_file, logger):
        
        # self.logger = logger
        # self.logger.info(f"Start translating {args.csvw_file} to SHACL")
        self.logger = logger
        # self.logger = create_logger(logger_file, "INFO")
        
        # self.logger.info(f"Start translating {args.csvw_file} to SHACL")

        self.csvw_file = csvw_file

        self.CSVW = json_load(csvw_file)
        self.folder_path = os.path.dirname(csvw_file)
        self.csv_file_location = csv_file_location

        if len(self.CSVW) == 0:
            empty_error(self.logger)
            
        self.translate()
        # Merge property shapes with the same path by adding sh:or constraint
        #TODO double check whether is necessary
        # self.SHACL = merge_property_shapes(self.SHACL)

        shaclValidation = Graph()
        shaclValidation.parse("https://www.w3.org/ns/shacl-shacl")

        r = validate(self.SHACL, shacl_graph=shaclValidation)
        if not r[0]:
            print(r[2])
        if output_file:
            self.writeShapeToFile(output_file)
        else:
            self.writeShapeToFile(csvw_file + ".shape.ttl")
        # print(self.SHACL.serialize(format="turtle"))
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Translate CSVW to SHACL')
    parser.add_argument("csvw_file",  help='csvw_file', type=str)
    args = parser.parse_args()

    C2S = CSVWtoSHACL()
    C2S.evaluate_file(args.csvw_file)
