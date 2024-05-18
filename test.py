from SCOOP.generator.jsonschema2shacl.src.json_schema_to_shacl import JsonSchemaToShacl, main
from SCOOP.generator.jsonschema2shacl.src.file_parser import parse_json_schema
from SCOOP.adjustment.shape_adjustment_jsonschema import ShapeAdjustment_JSONSchema
from rdflib import Graph

file_path = "test.json"

schema = parse_json_schema(file_path)

json_converter = JsonSchemaToShacl()

if schema is not None:
    json_converter.translate(schema)
    file_name = f"{file_path}.shape.ttl"
    json_converter.shacl.serialize(format="turtle", destination=file_name)

sa = ShapeAdjustment_JSONSchema("json",json_converter.names)
jsonschema_shape_g = Graph().parse("test.json.shape.ttl", format='turtle')
sa.parseRawDataSchemaShape(jsonschema_shape_g)

rml_shape_g = Graph().parse("test.rml.ttl", format='turtle')
sa.parseRML(rml_shape_g)
sa.adjust(jsonschema_shape_g)
sa.writeShapeToFile("test.json.shape.adjusted.ttl")