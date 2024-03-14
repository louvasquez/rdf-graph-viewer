#!/usr/bin/env python

import json
from pyvis.network import Network
import networkx as nx
import rdflib
import sys
import yaml

# cmdline args
graph_file = sys.argv[1] if len(sys.argv)>1 else None
config_file = sys.argv[2] if len(sys.argv)>2 else None

# get configs
configs = yaml.safe_load(open(config_file)) if config_file else {}
prefixes = configs['extra_prefixes'] if (configs is not None and 'extra_prefixes' in configs) else {}

# pull input graph file/info
g = rdflib.Graph()
g.parse(graph_file)
for (ns,iri) in g.namespaces():
    if str(iri) not in prefixes:
        prefixes[str(iri)] = ns

def is_hash(s):
    """ Cheap uuid/hash checkeer. Should match java UUIDs, maybe others
    """
    return ( len(s)>20
            and len([ c for c in s if c=='-'])>=3
            and s.lower() == s )
def is_filtered(filters,triple):
    """
    Check for any filter string in any element of triple

    Args:
        filters (list): List of strings to look for in triple
        triple (3-tuple): triple (s,p,o) as tuple
    
    Returns:
        boolean: whether string is found in any tuple element
    """
    return any(
        [ f in 
         "|".join( [ str(e) for e in (s,p,o) ] )
         for f in filters ] )

def cleanup_label(o,hashes,literals):   # node object
    """ Transforms node and edge label for all features 
    including (prefixes, literals, hashes)
    """
    o_s = str(o)
    # literals
    if type(o) == rdflib.term.Literal:
        literals[o_s] = literals.get(o_s,0)+1
        o_s = f'L({literals[o_s]}) {o_s}'
    # prefixes
    for p,v in prefixes.items():
        if p in o_s:
            o_s = o_s.replace(p,f"{v}:")
    # replace hashes as full IRI element (path segment)
    for e in o_s.split('/'):
        if is_hash(e):
            hashes += [e] if not e in hashes else []
            o_s = o_s.replace(e,f'H({str(hashes.index(e))})')
    return o_s

# the thing!
ng = nx.cycle_graph(0)

# thread unsafely prep
hashes = []
literals = {}
nodes = []
props = {}
filter = configs.get('filter',None)
# parse graph triples into networkx graph
for (s,p,o) in g:
    # subject may already be in graph
    if filter != None:
        if is_filtered(filter,(s,p,o)):
            continue
    if not s in nodes:
        full = str(s)
        s = cleanup_label(s,hashes,literals)            
        nodes += [s]
        ng.add_node(nodes.index(s),label=s,title=full)
    i1 = nodes.index(s)
    # object may already be in node
    if not o in nodes:
        full = str(o)
        o = cleanup_label(o,hashes,literals)
        nodes += [o]
        ng.add_node(nodes.index(o),label=o,title=full)
    # add edge
    i1 = nodes.index(s)
    i2 = nodes.index(o)
    ng.add_edge(i1,i2,label=cleanup_label(p,hashes,literals),title=str(p))

# moves desired edges into node label
# converts edges to proprties ("propertize" them)
# - list of edge labels
# e.g.
#   For A(label1) --prop1--> B(label2)
#   if 'prop1' is in list, B will be added to A's label
#   
#   resulting node will be
#       A(label1 <return> label2)
#   with node B removed, and Bs label appended to A
propertizes = configs.get('propertize',None)
if propertizes != None:
    
    # need to collect changes to make AFTER loop
    # changing things while iterating nodes breaks loop

    # keys are nodes, values are list of (name,value) pairs to add to node
    props2add = {}
    # list of nodes to remove (edges consumed into label)
    nodes2remove = set()  

    # iterate all edges
    for e,v in nx.edges(ng).items():
        print(e,v)
        # check edge against edge names we want to propertize
        for edge_name in propertizes:
            print("checking edge label:",v['label'])
            if edge_name in v['label']:
                if e[0] not in props2add:
                    props2add[e[0]] = {}
                props2add.get(e[0],{}).update(
                    { v['label']: nx.nodes(ng)[e[1]]['label'] }
                )
                nodes2remove.add(e[1])
    # print("props to add",props2add)
    # print("nodes to remove",nodes2remove)

    # NOW we can change the graph (add properties, remove far nodes)
    for n,props in props2add.items():
        for k,v in props.items():
            nx.nodes(ng)[n]['title'] += '\n'+k+" = "+v
    for n in nodes2remove:
        ng.remove_node(n)
            

# overrides node label by 'child' label with desired edge label
#   intended for RDF where literal of object has objects desired name
#   conversion of RDF to nodelike pyvis, requires using labels vs RDF-like things
# e.g.: for
#   A--(edge[label=first_name])-->B[label=bob]
#   if label 'first_name' is in overrides list, A will get B's label (bob)
# works for RDF where object's preferred name is in subject with known predicate
# e.g.
#   A --(hasName)--> B
#   an override filter item of 'hasName' will take B's label and place it on A
# - this is all due to RDF/LPG impedance mismatch
# - may want to handle in triples as RDF graph eventually BEFORE converting to pyvis graph
# - need to extend for other attributes?
overrides = configs.get('label_overrides',None)
if overrides != None:
    removals = []
    for edge_label in overrides:
        for e,v in nx.edges(ng).items():
            if edge_label in v['label']:
                # get child node label and place on parent
                ng.nodes()[e[0]]['label'] = ng.nodes()[e[1]]['label']
                removals.append(e[1])
    for nr in removals:
        ng.remove_node(nr)

# display graph using pyvis network
nt = Network(
    configs.get('height_px','1000px'),
    configs.get('width_px','1500px'),
    filter_menu=configs.get('filter_menu',True),
    select_menu=configs.get('select_menu',True),
    cdn_resources='in_line')
#nt.show_buttons(filter_=["physics"])
nt.show_buttons(configs.get('show_buttons',True))
nt.from_nx(ng)

if 'pyvis_config_options' in configs:
    nt.set_options(json.dumps(configs['pyvis_config_options']))

#if 'pyvis_config_options_json' in configs:
    #options="var options = "+configs['pyvis_config_options_json']
    #print(options)
if 'pyvis_config_options_json' in configs:
    print("setting config options")
    nt.set_options(configs['pyvis_config_options_json'])
nt.write_html('graph.html')
#nt.show('graph.html',notebook=False)


# output mappings (embedded in visual graph)
for i,hash in enumerate(hashes):
    print(f'HASH ({i}): {hash}')

