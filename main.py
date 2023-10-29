import sys 
import os
import argparse
import logging
import uuid
import time
import datetime
from rdflib import Graph
from pyshacl import validate
from src.shape_integration import ShapeIntegration

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Shape Integration')
    parser.add_argument('--shapes', type=str, nargs='+', help='List of shapes to be integrated')
    parser.add_argument('--output', type=str, help='Output file', default='shape_integration.ttl')
    args = parser.parse_args()

    # Logging
    log_file_name = f"log_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')}.log"
    # logging.basicConfig(filename=log_file_name, level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.info('Started')

    # Read shapes
    shapes = []
    validation_shape_graph = Graph().parse("shacl-shacl.ttl", format="turtle")
    for shape in args.shapes:
        print("Start reading shape %s", shape)
        try:
            g = Graph().parse(shape, format='turtle')
            r = validate(g, shacl_graph=validation_shape_graph, ont_graph=None,
                            inference='rdfs', abort_on_first=False, meta_shacl=False, debug=False)
            if not r[0]:
                print(r[2])
                sys.exit(1)
        except:
            logging.error('Error reading shape %s', shape)
            sys.exit(1)
        shapes.append(g)

    # Shape integration
    start_time = time.time()
    shIn = ShapeIntegration(shapes, args.output)
    shIn.integration()
    logging.info('Shape integration took %s seconds', time.time() - start_time)