from collections import namedtuple

from lxml import etree
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, SKOS
from pathlib import Path
import os

ConceptScheme = namedtuple("ConceptScheme", ["conceptScheme", "concepts", "metadata"])
SchemeData = namedtuple("SchemeData", ["id", "label", "definition"])
LangString = namedtuple("LangString", ["value", "lang"])
MetaString = namedtuple("MetaString",["cat", "d", "value"])

xml_file = [f for f in os.listdir('.') if f.endswith('.xml')]
if(len(xml_file) != 1):
    raise ValueError("There should be exactly one xml file in the directory")
filename = xml_file[0]

output_folder = Path("./data")
if not output_folder.exists():
    output_folder.mkdir()

def getValues(entry):
    if entry is not None:
        lang = entry.get("{http://www.w3.org/XML/1998/namespace}lang")
        value = entry.text
        return LangString(value, lang)
    else:
        return
def getMetaData(entry):
    if entry is not None:
        d = entry.get("def")
        cat = entry.get("cat")
        value = entry.text
        return MetaString(cat,d, value)

def parseXml():
    tree = etree.parse(filename)
    md_lists = tree.xpath("//MDDef")

    conceptSchemes = []
    # get labels and values
    for item in md_lists:
        # get concept scheme id
        _id = str(item.get("id"))
        # get label
        label = getValues(item.find("Label"))
        definition = getValues(item.find("Description"))

        metadata = item.find("MDDefMetadata")
        md = []
        for m in metadata:
            md.append(getMetaData(m))
        # get values
        # <Value id="1"><Label xml:lang="de">K1</Label><Description xml:lang="de">Mathematisch argumentieren</Description></Value>
        conceptScheme = SchemeData(_id, label, definition)

        values = item.findall("Value")
        concepts = []
        for value in values:
            _id = str(value.get("id"))
            label = getValues(value.find("Label"))
            definition = getValues(value.find("Description"))
            concepts.append(SchemeData(_id, label, definition))
        conceptSchemes.append(ConceptScheme(conceptScheme=conceptScheme, concepts=concepts,metadata=md))

    return conceptSchemes


def buildGraph(cs):
    conceptScheme = cs.conceptScheme
    concepts = cs.concepts
    metadata = cs.metadata
    cat = 0
    d = 0
    value = 0
    for md in metadata:
        cat = md.cat
        d = md.d
        value = md.value


    g = Graph()
    base_url = URIRef("http://example.org/iqb/cs_" + conceptScheme.id + "/")
    
    g.add((base_url, RDF.type, SKOS.ConceptScheme))
    g.add((base_url, DCTERMS.creator, Literal("IQB - Institut zur Qualitätsentwicklung im Bildungswesen", lang="de")))
    g.add((base_url, DCTERMS.title, Literal(conceptScheme.label.value, lang=conceptScheme.label.lang )))
    if conceptScheme.definition:
        g.add((base_url, DCTERMS.description, Literal(conceptScheme.definition.value, lang=conceptScheme.definition.lang)))
        
        
        g.add((base_url, SKOS.definition, Literal("cat: " + cat + " Def:" + d + " Value:" + value, lang="de")))
        
        g.add((base_url, SKOS.relatedMatch, Literal("https://huaning-yang.github.io/test-repo-core/index.de.html", lang="de")))

    for concept in concepts:
        concept_url = base_url + concept.id
        g.add((concept_url, RDF.type, SKOS.Concept))
        g.add((concept_url, SKOS.prefLabel, Literal(concept.label.value, lang=concept.label.lang)))
        if concept.definition:
            g.add((concept_url, SKOS.definition, Literal(concept.definition.value, lang=concept.definition.lang)))
        # add topConceptOf
        g.add((concept_url, SKOS.topConceptOf, base_url))
        g.add((base_url, SKOS.hasTopConcept, concept_url))
    
    
    
    g.bind("skos", SKOS)
    g.bind("dct", DCTERMS)

    outfile_path = output_folder / ("iqb_cs" + conceptScheme.id + ".ttl")
    g.serialize(str(outfile_path), format="turtle", base=base_url, encoding="utf-8")

conceptSchemes = parseXml()

for item in conceptSchemes:
    buildGraph(item)
