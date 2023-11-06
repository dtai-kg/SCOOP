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

from src.shape_generator.owl2shacl.src.OWLtoSHACL import translateFromUrl, translateFromFile, translateByJar

from src.shape_generator.xsd2shacl.src.XSDtoSHACL import XSDtoSHACL

import multiprocessing as mp


def extract_shape_rml(rml_files):
    shacl_files = []
    for i in range(len(rml_files)):
        mapping_file = rml_files[i]
        shacl_file = f'temp/rml{i}.ttl'
        try:
            print("Translating RML file ", mapping_file)
            RtoS = RMLtoSHACL()
            RtoS.evaluate_file(mapping_file,shacl_file)
            shacl_files.append(shacl_file)
        except:
            print("Error translating RML file ", mapping_file)
    print("=======Stored RML-driven SHACL shapes in ", shacl_files)
    # output_queue.put(('rml', shacl_files))
    return shacl_files


def extract_shape_ontology(owl_files):
    shacl_files = []
    for i in range(len(owl_files)):
        owl_file = owl_files[i]
        shacl_file = f'temp/owl{i}.ttl'        
        try:
            translateByJar(owl_file, shacl_file)
        except:
            print("Error translating ontology to SHACL shape by JAR, trying REST API now")
            translateFromFile(owl_file, shacl_file)
        shacl_files.append(shacl_file)
    print("=======Stored ontology-driven SHACL shapes in ", shacl_files)
    # output_queue.put(('ontology', shacl_files))
    return shacl_files

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
                        print("Adjusting shape :", rml)
                        rml_shape_g = Graph().parse(rml, format='turtle')
                        sa.parseRML(rml_shape_g)
                        sa.adjust(Graph()+xsd_shape_g)
                    except:
                        print("Error adjusting shape :", rml)
                sa.writeShapeToFile(shacl_file)
            shacl_files.append(shacl_file)
        except:
            print("Error translating XSD file :", xsd_file)
    print("=======Stored XSD-driven SHACL shapes in ", shacl_files)
    # output_queue.put(('xsd', shacl_files))
    return shacl_files

def integrate_shapes(shapes, output_file):
    shapes_graph = []
    validation_shape_graph = Graph().parse("shacl-shacl.ttl", format="turtle")
    for shape in shapes:
        print("Start reading shape :", shape)
        try:
            g = Graph().parse(shape, format='turtle')
        except:
            print('Error reading shape :', shape)

        shapes_graph.append(g)

    # Shape integration
    start_time = time.time()
    shIn = ShapeIntegration(shapes_graph, output_file)
    shIn.integration()
    print('Shape integration took %s seconds', time.time() - start_time)
    print("Saved final file in ", output_file)

def extractShapeParallel(input_files:tuple):
    file_type, files = input_files[0]
    if file_type == 'rml':
        shacl_files = extract_shape_rml(files)
        return ['rml', shacl_files]
    elif file_type == 'ontology':
        shacl_files = extract_shape_ontology(files)
        return ['ontology', shacl_files]
    elif file_type == 'xsd':
        files, rml_files = files
        shacl_files = extract_shape_xsd(files, rml_files)
        return ['xsd', shacl_files]

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
    input_files = []
    if args.rml:      
        rml_files = []
        for rml in args.rml:
            if os.path.isdir(rml):
                rml_files.extend([os.path.join(rml, f) for f in os.listdir(rml) if f.endswith('.ttl')])
            else:
                rml_files.append(rml)
        input_files.append([('rml', rml_files)])
    else:
        rml_files = []

    if args.ontology:
        owl_files = []
        for owl in args.ontology:
            if os.path.isdir(owl):
                owl_files.extend([os.path.join(owl, f) for f in os.listdir(owl) if f.endswith('.owl') or f.endswith('.ttl') or f.endswith('.rdf')])
            else:
                owl_files.append(owl)
        input_files.append([('ontology', owl_files)])
    if args.xsd:
        xsd_files = []
        for xsd in args.xsd:
            if os.path.isdir(xsd):
                xsd_files.extend([os.path.join(xsd, f) for f in os.listdir(xsd) if f.endswith('.xsd') or f.endswith('.xml')])
            else:
                xsd_files.append(xsd)
        input_files.append([('xsd', (xsd_files, rml_files))])
    
    # Parallelize the extraction of SHACL shapes from diverse sources

    mp_number = sum(1 for item in [args.rml, args.ontology, args.xsd] if item is not None)
    
    pool = mp.Pool(processes=mp_number)   
    print("Number of processes: ", mp_number)

    results = pool.map(extractShapeParallel, input_files)
    pool.close()
    pool.join()

    shapes = []
    for p in args.priority:
        for result in results:
            if p == result[0]:
                shapes.extend(result[1])

    print("Start integrating shapes")
    integrate_shapes(shapes, args.output)

    total_end_time = time.time()    
    

    print("Cleaning temp folder")
    for f in os.listdir("temp"):
        os.remove(os.path.join("temp", f))

    print("Total time: ", total_end_time - total_start_time)