import sys 
import os
import argparse
import logging
import uuid
import time
import datetime
from rdflib import Graph
from src.shape_integration import shapeIntegration

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
    for shape in args.shapes:
        try:
            shapes.append(Graph().parse(shape, format='turtle'))
        except:
            logging.error('Error reading shape %s', shape)
            sys.exit(1)

    # Shape integration
    start_time = time.time()
    shIn = shapeIntegration(shapes)
    shIn.integration()
    logging.info('Shape integration took %s seconds', time.time() - start_time)

    # Write output