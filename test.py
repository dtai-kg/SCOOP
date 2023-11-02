import re

xpath_tokenizer_re = re.compile(
    r"("
    r"'[^']*'|\"[^\"]*\"|"
    r"::|"
    r"//?|"
    r"\.\.|"
    r"\(\)|"
    r"!=|"
    r"[/.*:\[\]\(\)@=])|"
    r"((?:\{[^}]+\})?[^/\[\]\(\)@!=\s]+)|"
    r"\s+"
    )

pattern = "OPTrack/OPTrackParameter[@ID='ITP_NomGauge' and @IsApplicable='Y']/@Value"
pattern = "parent::*/UniqueOPID/@Value"
pattern = "http://trans.example.com/{route/stop/@id}/{route/stop}"
pattern = "http://data.europa.eu/949/functionalInfrastructure/tracks/{parent::OPTrack/parent::*/UniqueOPID/@Value}_{parent::OPTrack/OPTrackIdentification/@Value}"
def parseTemplate_xml(template):
    """
    A function to parse the template in a triples map and return path list
    """
    pattern = r'\{([^}]+)\}'
    matches = re.findall(pattern, template)
    matches = ["iterator"+"/"+i.replace("@","") for i in matches]

    return [matches]

print(parseTemplate_xml(pattern))

# for token in xpath_tokenizer_re.findall(pattern):
#     ttype, tag = token
#     if ttype:
#         print("ttype:-----", ttype)
#     if tag:
#         print("tag:-----", tag)