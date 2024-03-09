#!/usr/bin/env python

import json
from pyvis.network import Network
import networkx as nx
import rdflib
import sys
import yaml

graph_file = sys.argv[1] if len(sys.argv)>1 else None
config_file = sys.argv[2] if len(sys.argv)>2 else None

configs = yaml.safe_load(open(config_file)) if config_file else {}
print("configs",configs)
prefixes = configs['extra_prefixes'] if (configs is not None and 'extra_prefixes' in configs) else {}

g = rdflib.Graph()
g.parse(graph_file)
for (ns,iri) in g.namespaces():
    if str(iri) not in prefixes:
        prefixes[str(iri)] = ns

ng = nx.cycle_graph(0)

def is_hash(s):
    return ( len(s)>20
            and len([ c for c in s if c=='-'])>=3
            and s.lower() == s )
def cleanup_label(o,hashes,literals):   # node object
    o_s = str(o)
    if type(o) == rdflib.term.Literal:
        literals[o_s] = literals.get(o_s,0)+1
        o_s = f'L({literals[o_s]}) {o_s}'
    for p,v in prefixes.items():
        if p in o_s:
            o_s = o_s.replace(p,f"{v}:")
    for e in o_s.split('/'):
        if is_hash(e):
            hashes += [e] if not e in hashes else []
            o_s = o_s.replace(e,f'hash({str(hashes.index(e))})')
    return o_s

# threadsafe?
hashes = []
literals = {}
nodes = []
props = {}
for (s,p,o) in g:
    if not s in nodes:
        s = cleanup_label(s,hashes,literals)
        nodes += [s]
        ng.add_node(nodes.index(s),label=s)
    i1 = nodes.index(s)
    if not o in nodes:
        o = cleanup_label(o,hashes,literals)
        nodes += [o]
        ng.add_node(nodes.index(o),label=o)
    i1 = nodes.index(s)
    i2 = nodes.index(o)
    ng.add_edge(i1,i2,label=cleanup_label(p,hashes,literals))

nt = Network('1000px', '1500px')
nt.show_buttons(filter_=["physics"])
nt.from_nx(ng)
nt.show('graph.html',notebook=False)

for i,hash in enumerate(hashes):
    print(f'HASH ({i}): {hash}')
