import sys 
import os
import argparse
import time
import datetime
from SCOOP.pipline import *


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Shape Integration')
    
    parser.add_argument('--mode', type=str, help='integration mode: priority, priorityR, or all', default="priority")
    parser.add_argument('--parallel', type=bool, help='parallel mode: True or False', default=False)
    parser.add_argument('--priority', type=str, nargs='+', help='List of priority for integrating shapes from diverse sources', default=['rml', 'ontology', 'xsd', 'csvw'])
    
    parser.add_argument('--mappings', '-m', type=str, nargs='+', help='Path to folder or mapping files to be translated')
    
    parser.add_argument('--ontology', '-o', type=str, nargs='+', help='Path to folder or ontology files to be translated')
    
    parser.add_argument('--xsd', '-x', type=str, nargs='+', help='Path to folder or xsd file to be translated')
    parser.add_argument('--xsd_rml', '-xr', type=str, nargs='+', help='Path to folder or rml file for post-adjustment of XSD-driven shape')
    
    parser.add_argument('--csvw', '-c', type=str, nargs='+', help='Path to folder or csvw file to be translated')
    parser.add_argument('--csvw_rml', '-cr', type=str, nargs='+', help='Path to folder or rml file for post-adjustment of CSVW-driven shape')
    
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