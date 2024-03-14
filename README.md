# Overview

Creates visual interactive graph (graph.html) from rdf file.
- any rdflib parsable input file
- pyvis Network visualizer

## features

- segments literals into distinct nodes (prefixed with `L(n)` to make unique)
- replaces typical long java UUID (see output for mapping)
- allows additional('extra') prefixes not in rdf (see config)
- permits filtering of triples by list of strings (see config)
- override of pyvis Network settings (see config)
- overrides node's label with subject for matching labels (see config) (RDF/LPG impedance mismatch)
- "propertizes" edges, converting edges into properties (see config)

# Details

## Using

`./graph_vis.py <rdf_like_file> <config_file>`

e.g.
`./graph_vis.py example_graph.ttl example_config`

## Output

- list of java hashes replaced

## TODO

- add color by node type
- propertize paths (not just directly connected nodes)
- generalize more things (output filename, ...)
- utilize more rdf native properties
- many more...