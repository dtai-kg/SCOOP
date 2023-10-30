from abc import ABC, abstractmethod, abstractstaticmethod
from typing import List, Dict, Any
from pprint import pprint
from json import dumps
from dataclasses import dataclass
from enum import Enum, auto

from rdflib.term import Identifier, URIRef, BNode, Literal


@dataclass(frozen=True, eq=True)
class Triple():
    s: Identifier
    p: Identifier
    o: Identifier

    def __post_init__(self):

        if not (isinstance(self.s, URIRef)) and not (isinstance(self.s, BNode)):
            raise Exception(f"Subject has to be an IRI or Blank {self.s}")
        if not isinstance(self.p, URIRef):
            raise Exception(f"Predicate has to be an IRI {self.p}")


# TermMaps models
@dataclass
class TermMap(ABC):
    iri: Identifier
    po_dict: Dict[URIRef, List[Any]]

    def __init__(self, iri: Identifier, po_dict: Dict[URIRef, List[Any]], **_):
        self.po_dict = po_dict
        self.iri = iri

    def __post_init__(self):
        if not (isinstance(self.iri, URIRef)) and not (isinstance(self.iri, BNode)):
            raise Exception(f"Subject of this TermMap has to be an IRI or Blank {self.iri.__repr__}")


class SubjectMap(TermMap):
    def identity(self):
        pass


class PredicateMap(TermMap):
    def identity(self):
        pass


class ObjectMap(TermMap):
    def identity(self):
        pass


class GraphMap(TermMap):
    def identity(self):
        pass


@dataclass
class PredicateObjectMap(TermMap):
    PM: PredicateMap
    OM: ObjectMap

    def identity(self):
        pass


# END TermMaps models


@dataclass
class LogicalSource(TermMap):
    iri: Identifier
    po_dict: Dict[URIRef, Any]


@dataclass
class TriplesMap():
    iri: Identifier
    sm: SubjectMap
    poms: List[PredicateObjectMap]
    logical_source: LogicalSource
    gm: GraphMap = None
    po_dict = Dict[URIRef, Any]


if __name__ == "__main__":
    print(URIRef("rr:template") == URIRef("rr:template"))

    sm = SubjectMap({
        URIRef("rr:template"): ["lqsdfijm?%lsdjf%"]
    })
    pm = PredicateMap({
        URIRef("rr:template"): ["lqsdfijm?%lsdjf%"]
    })
    om = ObjectMap({
        URIRef("rr:template"): ["lqsdfijm?%lsdjf%"]
    })

    logical_source = Triple(URIRef("lksdjflj"), URIRef(
        "klsjdf"), Literal("klsdjlfj"))
    gm = GraphMap({
        URIRef("rr:template"): ["lqsdfijm?%lsdjf%"]
    })

    pom = PredicateObjectMap(po_dict={}, PMs=[pm], OMs=[om])

    TM = TriplesMap(sm, [pom], logical_source)

    pprint(TM)
