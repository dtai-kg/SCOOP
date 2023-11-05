import sys 
import os
import argparse
import logging
import time
import datetime
from rdflib import Graph
from pyshacl import validate
from src.shape_integration import ShapeIntegration
from src.shape_adjustment_single import ShapeAdjustment

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from src.shape_generator.rml2shacl.src.RML import *
from src.shape_generator.rml2shacl.src.RMLtoShacl import RMLtoSHACL
from src.shape_generator.rml2shacl.src.SHACL import *

from src.shape_generator.xsd2shacl.src.XSDtoSHACL import XSDtoSHACL

def extract_shape_rml(rml_files):
    shacl_files = []
    for i in range(len(rml_files)):
        mapping_file = rml_files[i]
        shacl_file = f'temp/rml{i}.ttl'
        try:
            RtoS = RMLtoSHACL()
            RtoS.evaluate_file(mapping_file,shacl_file)
            shacl_files.append(shacl_file)
        except:
            print("Error translating RML file ", mapping_file)
    print("=======Stored RML-driven SHACL shapes in ", shacl_files)
    return shacl_files


def extract_shape_ontology(ontology):
    pass

def extract_shape_xsd(xsd_files, rml_files=[]):
    shacl_files = []
    for i in range(len(xsd_files)):
        xsd_file = xsd_files[i]
        shacl_file = f'temp/xsd{i}.ttl'
        try:
            X2S = XSDtoSHACL()
            X2S.evaluate_file(xsd_file, shacl_file)
            if rml_files != []:
                print("Start adjusting shape")
                sa = ShapeAdjustment("xml")
                xsd_shape_g = Graph().parse(shacl_file, format='turtle')
                sa.parseRawDataSchemaShape(xsd_shape_g)
                for rml in rml_files:
                    try:
                        rml_shape_g = Graph().parse(rml, format='turtle')
                        sa.parseRML(rml_shape_g)
                        sa.adjust(Graph()+xsd_shape_g)
                    except:
                        print("Error adjusting shape ", rml)
                sa.writeShapeToFile(shacl_file)
            shacl_files.append(shacl_file)
        except:
            print("Error translating XSD file ", xsd_file)
    print("=======Stored XSD-driven SHACL shapes in ", shacl_files)
    return shacl_files

def integrate_shapes(shapes, output_file):
    shapes_graph = []
    validation_shape_graph = Graph().parse("shacl-shacl.ttl", format="turtle")
    for shape in shapes:
        print("Start reading shape %s", shape)
        try:
            g = Graph().parse(shape, format='turtle')
            r = validate(g, shacl_graph=validation_shape_graph, ont_graph=None,
                            inference='rdfs', abort_on_first=False, meta_shacl=False, debug=False)
            if not r[0]:
                print(r[2])
                sys.exit(1)
        except:
            print('Error reading shape %s', shape)

        shapes_graph.append(g)

    # Shape integration
    start_time = time.time()
    shIn = ShapeIntegration(shapes_graph, output_file)
    shIn.integration()
    print('Shape integration took %s seconds', time.time() - start_time)
    print("Saved final file in ", output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Shape Integration')
    parser.add_argument('--priority', '-p', type=str, nargs='+', help='List of priority for integrating shapes from diverse sources', default=['rml', 'ontology', 'xsd'])
    parser.add_argument('--rml', '-r', type=str, nargs='+', help='Path to folder or rml files to be translated')
    parser.add_argument('--ontology', '-owl', type=str, nargs='+', help='Path to folder or owl files to be translated')
    parser.add_argument('--xsd', '-x', type=str, nargs='+', help='Path to folder or xsd file to be translated')
    parser.add_argument('--output', '-o', type=str, help='Output file', default='shape_integration.ttl')
    args = parser.parse_args()

    if not os.path.exists("temp"):
        os.mkdir("temp")
    
    total_start_time = time.time()
    print("Start translating shapes")
    shapes = []
    for p in args.priority:
        if p == 'rml' and args.rml:
            print("Start translating rml")
            files = []
            for rml in args.rml:
                if os.path.isdir(rml):
                    files.extend([os.path.join(rml, f) for f in os.listdir(rml) if f.endswith('.ttl')])
                else:
                    files.append(rml)
            shapes.extend(extract_shape_rml(files))
            print("Finish translating rml")

        elif p == 'ontology' and args.ontology:
            print("Start translating ontology")
            files = []
            for owl in args.ontology:
                if os.path.isdir(owl):
                    files.extend([os.path.join(owl, f) for f in os.listdir(owl) if f.endswith('.owl')])
                else:
                    files.append(owl)
            shapes.extend(extract_shape_ontology(args.ontology))
            print("Finish translating ontology")

        elif p == 'xsd' and args.xsd:
            print("Start translating xsd")
            files = []
            for xsd in args.xsd:
                if os.path.isdir(xsd):
                    files.extend([os.path.join(xsd, f) for f in os.listdir(xsd) if f.endswith('.xsd') or f.endswith('.xml')])
                else:
                    files.append(xsd)
            shapes.extend(extract_shape_xsd(files))
            print("Finish translating xsd")

    print("Start integrating shapes")
    integrate_shapes(shapes, args.output)

    total_end_time = time.time()    
    

    print("Cleaning temp folder")
    for f in os.listdir("temp"):
        os.remove(os.path.join("temp", f))

    print("Total time: ", total_end_time - total_start_time)