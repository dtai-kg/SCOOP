import sys 
import os
import argparse
import logging
import time
import datetime
from rdflib import Graph
from pyshacl import validate
import multiprocessing as mp
from SCOOP.shape_integration_priority import ShapeIntegrationPriority
from SCOOP.shape_integration_priority_r import ShapeIntegrationPriorityR
from SCOOP.shape_integration_all import ShapeIntegrationAll
from SCOOP.shape_adjustment_single import ShapeAdjustment

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from SCOOP.shape_generator.rml2shacl.src.RML import *
from SCOOP.shape_generator.rml2shacl.src.RMLtoShacl import RMLtoSHACL
from SCOOP.shape_generator.rml2shacl.src.SHACL import *

from SCOOP.shape_generator.owl2shacl.src.OWLtoSHACL import translateFromUrl, translateFromFile, translateByJar

from SCOOP.shape_generator.xsd2shacl.src.XSDtoSHACL import XSDtoSHACL

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
    return shacl_files

def integrate_shapes(shapes, output_file, mode):
    shapes_graph = []
    # validation_shape_graph = Graph().parse("shacl-shacl.ttl", format="turtle")
    for shape in shapes:
        print("Start reading shape :", shape)
        try:
            g = Graph().parse(shape, format='turtle')
        except:
            print('Error reading shape :', shape)

        shapes_graph.append((g,shape))

    # Shape integration
    if mode == 'priority':
        print("Start integrating shapes with priority")
        start_time = time.time()
        shIn = ShapeIntegrationPriority(shapes_graph, output_file)
        shIn.integration()
        print('Shape integration took %s seconds', time.time() - start_time)
        print("Saved final file in ", output_file)

    elif mode == 'priorityR':
        print("Start integrating shapes with priority restricted")
        start_time = time.time()
        shIn = ShapeIntegrationPriorityR(shapes_graph, output_file)
        shIn.integration()
        print('Shape integration took %s seconds', time.time() - start_time)
        print("Saved final file in ", output_file)

    elif mode == 'all':
        print("Start integrating shapes with all")
        start_time = time.time()
        shIn = ShapeIntegrationAll(shapes_graph, output_file)
        shIn.integration()
        print('Shape integration took %s seconds', time.time() - start_time)
        print("Saved final file in ", output_file)

def extract_preliminary_shapes(args):
    if not os.path.exists("temp"):
        os.mkdir("temp")
    
    
    shapes = []

    for p in args.priority:
        if p == 'rml' and args.mappings:
            print("Start translating rml")
            rml_files = []
            for rml in args.mappings:
                if os.path.isdir(rml):
                    rml_files.extend([os.path.join(rml, f) for f in os.listdir(rml) if f.endswith('.ttl')])
                else:
                    rml_files.append(rml)
            rml_shacl_files = extract_shape_rml(rml_files)
            shapes.extend(rml_shacl_files)
            print("Finish translating rml")

        elif p == 'ontology' and args.ontology:
            print("Start translating ontology")
            owl_files = []
            for owl in args.ontology:
                if os.path.isdir(owl):
                    owl_files.extend([os.path.join(owl, f) for f in os.listdir(owl) if f.endswith('.owl') or f.endswith('.ttl') or f.endswith('.rdf')])
                else:
                    owl_files.append(owl)
            owl_shacl_files = extract_shape_ontology(owl_files)
            shapes.extend(owl_shacl_files)
            print("Finish translating ontology")

        elif p == 'xsd' and args.xsd:
            print("Start translating xsd")
            xsd_files = []
            for xsd in args.xsd:
                if os.path.isdir(xsd):
                    xsd_files.extend([os.path.join(xsd, f) for f in os.listdir(xsd) if f.endswith('.xsd') or f.endswith('.xml')])
                else:
                    xsd_files.append(xsd)
     
            if args.xsd_rml:
                print("Start translating rml for post-adjustment of XSD-driven shape")
                xsd_rml_files = []
                for rml in args.xsd_rml:
                    if os.path.isdir(rml):
                        xsd_rml_files.extend([os.path.join(rml, f) for f in os.listdir(rml) if f.endswith('.ttl') or f.endswith('.rml')])
                    else:
                        xsd_rml_files.append(rml)
                xsd_shacl_files = extract_shape_xsd(xsd_files, xsd_rml_files)
            else:
                xsd_shacl_files = extract_shape_xsd(xsd_files)
            shapes.extend(xsd_shacl_files)
            print("Finish translating xsd")
    return shapes

def extractShape4Parallel(input_files:tuple):
    file_type, files = input_files[0]
    if file_type == 'rml':
        start_rml_time = time.time()
        shacl_files = extract_shape_rml(files)
        print("RML2SHACL execution time: ", time.time() - start_rml_time)
        return ['rml', shacl_files]
    elif file_type == 'ontology':
        start_ontology_time = time.time()
        shacl_files = extract_shape_ontology(files)
        print("OWL2SHACL execution time: ", time.time() - start_ontology_time)
        return ['ontology', shacl_files]
    elif file_type == 'xsd':
        files, rml_files = files
        start_xsd_time = time.time()
        shacl_files = extract_shape_xsd(files, rml_files)
        print("XSD2SHACL execution time: ", time.time() - start_xsd_time)
        return ['xsd', shacl_files]

def extract_preliminary_shapes_parallel(args):
    shapes, rml_files, owl_files, xsd_files, xsd_rml_files = [], [], [], [], []
    if args.mappings:      
        for rml in args.mappings:
            if os.path.isdir(rml):
                rml_files.extend([os.path.join(rml, f) for f in os.listdir(rml) if f.endswith('.ttl')])
            else:
                rml_files.append(rml)
        shapes.append([('rml', rml_files)])

    if args.ontology:
        for owl in args.ontology:
            if os.path.isdir(owl):
                owl_files.extend([os.path.join(owl, f) for f in os.listdir(owl) if f.endswith('.owl') or f.endswith('.ttl') or f.endswith('.rdf')])
            else:
                owl_files.append(owl)
        shapes.append([('ontology', owl_files)])

    if args.xsd:
        for xsd in args.xsd:
            if os.path.isdir(xsd):
                xsd_files.extend([os.path.join(xsd, f) for f in os.listdir(xsd) if f.endswith('.xsd') or f.endswith('.xml')])
            else:
                xsd_files.append(xsd)
        if args.xsd_rml:
            for rml in args.xsd_rml:
                if os.path.isdir(rml):
                    xsd_rml_files.extend([os.path.join(rml, f) for f in os.listdir(rml) if f.endswith('.ttl') or f.endswith('.rml')])
                else:
                    xsd_rml_files.append(rml)
        shapes.append([('xsd', (xsd_files, xsd_rml_files))])
    
    # parallel
    mp_number = sum(1 for item in [args.mappings, args.ontology, args.xsd] if item is not None)
    pool = mp.Pool(processes=mp_number)   
    print("Number of processes: ", mp_number)
    results = pool.map(extractShape4Parallel, shapes)
    pool.close()
    pool.join()

    shapes = []
    for p in args.priority:
        for result in results:
            if p == result[0]:
                shapes.extend(result[1])
    
    return shapes

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Shape Integration')
    parser.add_argument('--mode', type=str, help='integration mode: priority, priorityR, or all', default="priority")
    parser.add_argument('--parallel', type=bool, help='parallel mode: True or False', default=False)
    parser.add_argument('--priority', type=str, nargs='+', help='List of priority for integrating shapes from diverse sources', default=['rml', 'ontology', 'xsd'])
    parser.add_argument('--mappings', '-m', type=str, nargs='+', help='Path to folder or mapping files to be translated')
    parser.add_argument('--ontology', '-o', type=str, nargs='+', help='Path to folder or ontology files to be translated')
    parser.add_argument('--xsd', '-x', type=str, nargs='+', help='Path to folder or xsd file to be translated')
    parser.add_argument('--xsd_rml', '-xr', type=str, nargs='+', help='Path to folder or rml file for post-adjustment of XSD-driven shape')
    parser.add_argument('--output', '-ot', type=str, help='Output file', default='shape_integration.ttl')
    args = parser.parse_args()

    total_start_time = time.time()
    if args.parallel:
        print("Start translating shapes in parallel...")
        shapes = extract_preliminary_shapes_parallel(args)
    else:
        print("Start translating shapes...")
        shapes = extract_preliminary_shapes(args)

    print("Start integrating shapes...")
    integrate_shapes(shapes, args.output, args.mode)

    total_end_time = time.time()    
    
    print("Cleaning temp folder...")
    for f in os.listdir("temp"):
        os.remove(os.path.join("temp", f))

    print("Total time: ", total_end_time - total_start_time)