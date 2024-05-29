from SCOOP.shape_adjustment_csvw import ShapeAdjustment
from rdflib import Graph
from SCOOP.shape_generator.csvw2shacl.src.CSVWtoSHACL import CSVWtoSHACL
from logger import create_logger
import argparse


# logger = create_logger("log.log", "INFO")
# C2S = CSVWtoSHACL()
# C2S.evaluate_file("test.json","",None,logger)

sa = ShapeAdjustment("csv")
csvw_shape_g = Graph().parse("test.json.shape.ttl", format='turtle')
sa.parseRawDataSchemaShape(csvw_shape_g)

rml_shape_g = Graph().parse("test.rml.ttl", format='turtle')
sa.parseRML(rml_shape_g)
sa.adjust(csvw_shape_g)
sa.writeShapeToFile("test.rml.adjusted.ttl")