
"""
Utiles functions for the CSVW2SHACL translation
"""

import json
import requests
import re
from collections import Counter
from rdflib import Graph, URIRef, Literal, BNode, RDF, RDFS, Namespace
SHACL = Namespace("http://www.w3.org/ns/shacl#")

def json_load(json_name):
    """
    Load a json file from a URL or a local file
    """
    if re.match(r'https?://', str(json_name)):
        return requests.get(json_name).json()
    with open(json_name, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_list_values(graph, list_head):
    """
    Extract the values of a RDF list in a graph
    """
    values = []
    while list_head != RDF.nil:
        list_item = graph.value(list_head, RDF.first)
        if list_item:
            values.append(list_item.value)
        list_head = graph.value(list_head, RDF.rest)
    return values

################################################################
####################### Update Graph ###########################
################################################################

def update_languageIn(g, subject, values):
    """
    Add the languageIn constraint with single or multiple language tags in the graph
    """
    current_BN = BNode()
    g.add((subject, SHACL.languageIn, current_BN))
    for index in range(len(values))[0:-1]:
        g.add((current_BN, RDF.first, Literal(values[index]))) 
        next_BN = BNode()
        g.add((current_BN, RDF.rest, next_BN)) 
        current_BN = next_BN

    g.add((current_BN, RDF.first, Literal(values[-1]))) 
    g.add((current_BN, RDF.rest, RDF.nil)) 
    return g 

def update_OrConstraint(g, subject, predicate, values, old_subjects):
    """
    Add the OrConstraint in the graph
    """
    unique_values = list(set(values))
    if len(unique_values) == 1 and len(values)==len(old_subjects):
        g.add((subject,predicate,unique_values[0]))
        return g
    elif len(unique_values) > 1:
        current_BN = BNode()
        g.add((subject, SHACL["or"], current_BN))
        for index in range(len(unique_values))[0:-1]:
            temp_bn = BNode()
            temp_triple = (temp_bn, predicate, URIRef(unique_values[index]))
            g.add(temp_triple)
            g.add((current_BN, RDF.first, temp_bn)) 
            next_BN = BNode()
            g.add((current_BN, RDF.rest, next_BN)) 
            current_BN = next_BN

        temp_bn = BNode()
        temp_triple = (temp_bn, predicate, URIRef(unique_values[-1]))
        g.add(temp_triple)
        g.add((current_BN, RDF.first, temp_bn)) 

        g.add((current_BN, RDF.rest, RDF.nil)) 
        return g 

def delete_triples(g, subject):
    """
    Delete all triples related to the subject
    """
    bnodes = []
    for s,p,o in g:
        if s == subject:
            g.remove((s,p,o))
            if isinstance(o,BNode):
                bnodes.append(o)
        elif o == subject:
            g.remove((s,p,o))
        if (s in bnodes) or (o in bnodes):
            if isinstance(o,BNode):
                bnodes.append(o)
            if isinstance(s,BNode):
                bnodes.append(s)
    for s,p,o in g:
        if (s in bnodes) or (o in bnodes):
            g.remove((s,p,o))
    return g

def update_graph(g,old_subjects,new_s):
    """
    Delete all triples related to the old subjects and replace the reference relationship with the new subject
    """
    bnodes = []
    for s,p,o in g:
        if s in old_subjects:
            g.remove((s,p,o))
            if isinstance(o,BNode):
                bnodes.append(o)
        elif o in old_subjects:
            g.remove((s,p,o))
            g.add((s, p, new_s))
        if (s in bnodes) or (o in bnodes):
            if isinstance(o,BNode):
                bnodes.append(o)
            if isinstance(s,BNode):
                bnodes.append(s)
    for s,p,o in g:
      if (s in bnodes) or (o in bnodes):
        g.remove((s,p,o))

    return g

def update_subject(g, old_s, new_s):
    """
    Update the old subject with new subject in the graph
    """
    triples_to_remove = []
    triples_to_add = []

    for s,p,o in g:
        if s == old_s:
            triples_to_remove.append((s,p,o))
            new_triple = (new_s, p, o)
            triples_to_add.append(new_triple)
        elif o == old_s:
            triples_to_remove.append((s,p,o))
            new_triple = (s, p, new_s)
            triples_to_add.append(new_triple)

    for triple in triples_to_remove:
        g.remove(triple)

    for triple in triples_to_add:
        g.add(triple)
    return g

def merge_property_shapes(g):
    """
    Merge property shapes with the same path
    """
    shapesTobecombined, path_list, triples = [], [], []
    path_triples = g.triples((None,  SHACL.path, None))
    ignore_list = [RDF.type, SHACL.path]
    for s, p, o in path_triples:
        triples.append((s,p,o))
        path_list.append(o)

    value_counts = Counter(path_list)
    duplicates = [value for value, count in value_counts.items() if count > 1]

    for path in duplicates:
        temp = []
        for s, p, o in triples:
            if o == path:
                temp.append(s)
        shapesTobecombined.append((temp,path))

    for old_subjects, path_value in shapesTobecombined:
        new_s = ""
        temp_dict = {}
        for old_s in old_subjects: 
          new_s+=str(old_s).split("/PropertyShape")[0]
        new_s = URIRef(new_s+"/PropertyShape")
        g.add((new_s,RDF.type,SHACL.PropertyShape))
        g.add((new_s,SHACL.path,path_value))
        for s, p, o in g:
            if (s in old_subjects) and (p not in ignore_list):
                if p == SHACL.languageIn:
                    language_list = extract_list_values(g, o)
                    t = temp_dict.get(p,[])
                    t.extend(language_list)
                    temp_dict[p] = t
                else:
                    t = temp_dict.get(p,[])
                    t.append(o)
                    temp_dict[p] = t
        # Update constraints
        for k,v in temp_dict.items():
            if k == SHACL.languageIn:
                g = update_languageIn(g, new_s, v)
            elif k == SHACL.datatype:
                g = update_OrConstraint(g, new_s, SHACL.datatype, v, old_subjects)

        g = update_graph(g, old_subjects, new_s)

    return g



################################################################
####################### URL Relevant ###########################
################################################################

def extract_paths(url):
    if url is None:
        return None
    if "{" in url:
        pattern = r"\{([^}]*)\}"
        matches = re.findall(pattern, url)
        return matches
    else:
        return url


def serializeTemplate(templateString):
    # we want to replace this {word} into a wildcard ='.'
    # and '*' means zero or unlimited amount of characters
    parts = templateString.split('{')
    parts2 = []
    for part in parts:
        if '}' in part:
            parts2 = parts2 + part.split('}')
        else:
            parts2 = parts2 + [part]
    string = ''
    tel = 1
    for part in parts2:
        if tel % 2 != 0:
            string = string + part
        else:
            string = string + '.*'
        # wildcard = '.' + '*'
        tel += 1
    resultaat = Literal(string)
    return resultaat