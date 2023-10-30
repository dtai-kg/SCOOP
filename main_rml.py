import sys 
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import argparse
import logging
import time 
from src.shape_generator.rml2shacl.src.RML import *
from src.shape_generator.rml2shacl.src.RMLtoShacl import RMLtoSHACL
from src.shape_generator.rml2shacl.src.SHACL import *

if __name__ == "__main__":
    
    RtoS = RMLtoSHACL()
    parser = argparse.ArgumentParser()
    parser.add_argument("MAPPING_FILE", type=str,
                        help="RML mapping file to be converted into SHACL shapes.")
    parser.add_argument("-SHACL_FILE", "-s", type=str, default="shapes/",
                        help="SHACL shape path")
    parser.add_argument("-logLevel", "-l", type=str, default="INFO",
                        help="Logging level of this script")

    args = parser.parse_args()

    loglevel = args.logLevel
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)

    start = time.time()
    if args.MAPPING_FILE is None:
        exit()
    else:
        RtoS.evaluate_file(args.MAPPING_FILE,args.SHACL_FILE)

    end = time.time()

    print(f"Elapsed time: {end - start} seconds")
