#################################################################
# draw_network.py 
# This program draws a network diagram, with manual intervention to
# improve the plotting.  It normally scales nodes by degree, but
# if you set "year_size" constant to be true, will scale them by
# year instead.  It makes two kinds of graphs, one colored by Louvain 
# partition and one by port of origin, and each one with and without lines.
# The Nat Comm paper used coloring by port.

# node size:  True scales by year, False by weighted degree of node
year_size = False

######################################################################

import csv
from operator import itemgetter
import networkx as nx
import community as community_louvain
import graph_tool as gt
import cairo

import pickle

###########################################################
# functions

def readivorypath(pathsfile):
  ivorypaths = {}
  inlines = open(pathsfile,"r").readlines()
  for line in inlines:
    pline = line.rstrip().split("\t")
    ivorypaths[pline[0]] = pline[1:]
  return ivorypaths

def convert_color(color):
  color = color.split(",")
  color = [int(x) for x in color]
  color = [hex(x) for x in color]
  color = [str(x) for x in color]
  finalcolor = "#"
  for entry in color:
    entry = entry[2:]
    if len(entry) == 1:
      entry = "0" + entry
    finalcolor = finalcolor + entry
  return(finalcolor)

def get_year(seizurename):
  # special case code, hopefully not needed anymore
  if seizurename == "PHL_2009_4.9t":  return 9
  date = seizurename.split("_")[1]
  year = int(date.split("-")[1])
  if year > 50:  year = 1900 + year
  else:  year = 2000 + year
  return year

def read_portcolors(name_to_num,num_to_port,colorfile):
  # read file of port color choices
  port_to_fill = {}
  port_to_text = {}
  for line in open(colorfile,"r"):
    if line.startswith("port"):  continue  # skip header
    port,fillcolor,textcolor = line.rstrip().split("\t")
    fillcolor = convert_color(fillcolor)
    textcolor = convert_color(textcolor)
    port_to_fill[port] = fillcolor
    port_to_text[port] = textcolor

  # set up dictionaries by seizure number
  filldict = {}
  textdict = {}
  sizedict = {}
  for name, num in name_to_num.items():
    port = num_to_port[num]
    year = get_year(name)
    fill = port_to_fill[port]
    text = port_to_text[port]
    filldict[num] = fill
    textdict[num] = text
    sizedict[num] = year
  return filldict,textdict,sizedict,port_to_fill

def install_partitions(graph,partitions):
  for key,partition in partitions.items():
    graph.nodes[key]["mary_partition"] = int(partition)
    graph.nodes[key]["mary_nodename"] = key
  
# remove low-weight edges, then remove any node not attached to anyone else
def trim_graph(nodes,edges,minlink):
  newedges = []
  mentioned_in_edges = set()
  for edge in edges:
    if edge[2] >= minlink:
      newedges.append(edge)
      mentioned_in_edges.add(edge[0])
      mentioned_in_edges.add(edge[1])
  newnodes = []
  for node in nodes:
    if node in mentioned_in_edges:
      newnodes.append(node)
  return newnodes,newedges


# functions from the net to convert networkx to graph-tools
def get_prop_type(value, key=None):
    """
    Performs typing and value conversion for the graph_tool PropertyMap class.
    If a key is provided, it also ensures the key is in a format that can be
    used with the PropertyMap. Returns a tuple, (type name, value, key)
    """
   # if isinstance(key, unicode):
    #    # Encode the key as ASCII
     #   key = key.encode('ascii', errors='replace')

    # Deal with the value
    if isinstance(value, bool):
        tname = 'bool'

    elif isinstance(value, int):
        tname = 'int'
        value = int(value)

    elif isinstance(value, float):
        tname = 'float'

    #elif isinstance(value, unicode):
     #   tname = 'string'
      #  value = value.encode('ascii', errors='replace')

    elif isinstance(value, dict):
        tname = 'object'

    else:
        tname = 'string'
        value = str(value)

    return tname, value, key


def nx2gt(nxG):
    """
    Converts a networkx graph to a graph-tool graph.
    """
    # Phase 0: Create a directed or undirected graph-tool Graph
    gtG = gt.Graph(directed=nxG.is_directed())

    # Add the Graph properties as "internal properties"
    for key, value in nxG.graph.items():
        # Convert the value and key into a type for graph-tool
        tname, value, key = get_prop_type(value, key)

        prop = gtG.new_graph_property(tname) # Create the PropertyMap
        gtG.graph_properties[key] = prop     # Set the PropertyMap
        gtG.graph_properties[key] = value    # Set the actual value

    # Phase 1: Add the vertex and edge property maps
    # Go through all nodes and edges and add seen properties
    # Add the node properties first
    nprops = set() # cache keys to only add properties once
    for node, data in nxG.nodes(data=True):

        # Go through all the properties if not seen and add them.
        for key, val in data.items():
            if key in nprops: continue # Skip properties already added

            # Convert the value and key into a type for graph-tool
            tname, _, key  = get_prop_type(val, key)

            prop = gtG.new_vertex_property(tname) # Create the PropertyMap
            gtG.vertex_properties[key] = prop     # Set the PropertyMap

            # Add the key to the already seen properties
            nprops.add(key)

    # Also add the node id: in NetworkX a node can be any hashable type, but
    # in graph-tool node are defined as indices. So we capture any strings
    # in a special PropertyMap called 'id' -- modify as needed!
    gtG.vertex_properties['id'] = gtG.new_vertex_property('string')

    # Add the edge properties second
    eprops = set() # cache keys to only add properties once
    for src, dst, data in nxG.edges(data=True):

        # Go through all the edge properties if not seen and add them.
        for key, val in data.items():
            if key in eprops: continue # Skip properties already added

            # Convert the value and key into a type for graph-tool
            tname, _, key = get_prop_type(val, key)

            prop = gtG.new_edge_property(tname) # Create the PropertyMap
            gtG.edge_properties[key] = prop     # Set the PropertyMap

            # Add the key to the already seen properties
            eprops.add(key)

    # Phase 2: Actually add all the nodes and vertices with their properties
    # Add the nodes
    vertices = {} # vertex mapping for tracking edges later
    #for node, data in nxG.nodes_iter(data=True):
    for node, data in nxG.nodes(data=True):

        # Create the vertex and annotate for our edges later
        v = gtG.add_vertex()
        vertices[node] = v

        # Set the vertex properties, not forgetting the id property
        data['id'] = str(node)
        for key, value in data.items():
            gtG.vp[key][v] = value # vp is short for vertex_properties

    # Add the edges
    # for src, dst, data in nxG.edges_iter(data=True):
    for src, dst, data in nxG.edges(data=True):

        # Look up the vertex structs from our vertices mapping and add edge.
        e = gtG.add_edge(vertices[src], vertices[dst])

        # Add the edge properties
        for key, value in data.items():
            gtG.ep[key][e] = value # ep is short for edge_properties

    # Done, finally!
    return gtG




#########################################################################
#### main program

import sys

if len(sys.argv) != 5:
  print("USAGE:  python3 draw_network.py minlink ivory_paths seizure_numbering.tsv layout.pkl")
  print("Uses files seizure_edges.csv, seizure_nodes.csv in the working directory")
  print("If you need a new layout, write None for layout.pkl")
  exit(-1)

minlink = float(sys.argv[1])
pathsfile = sys.argv[2]
numfile = sys.argv[3]
if sys.argv[4] == "None":
  layoutfilename = None
else:
  layoutfilename = sys.argv[4]

pathdir = readivorypath(pathsfile)
ivory_dir = pathdir["ivory_pipeline_dir"][0]

nodefile = "seizure_nodes.csv"
edgefile = "seizure_edges.csv"
colorfile = ivory_dir + "aux/port_colors.tsv"

####
# read file that relates name, number, and port
name_to_num = {}
num_to_name = {}
num_to_port = {}
for line in open(numfile,"r"):
  if line.startswith("Seizure"):  continue   # skip header
  line = line.rstrip().split("\t")
  name_to_num[line[0]] = line[1]
  num_to_name[line[1]] = line[0]
  num_to_port[line[1]] = line[2]

####
# read node and edge data (normally written by phase4.py)
with open(nodefile,"r") as nodecsv:
  nodereader = csv.reader(nodecsv)
  nodes = [n for n in nodereader][1:]
for node in nodes:
  if node[0] not in name_to_num:
    print("Unable to find seizure",node[0],"in file",numfile)
    print("If you have added seizures since this file was created,")
    print("you will need to update it with the new seizures, giving")
    print("each one a unique number")
    exit(-1)
nodes = [name_to_num[n[0]] for n in nodes]
print("Found",len(nodes),"nodes")

with open(edgefile,"r") as edgecsv:
  edgereader = csv.reader(edgecsv)
  edges = [tuple(e[0:3]) for e in edgereader][1:]
newedges = []
for edge in edges:
  newedge = (name_to_num[edge[0]],name_to_num[edge[1]],float(edge[2]))
  newedges.append(newedge)
edges = newedges
print("Found",len(edges),"edges")

nodes,edges = trim_graph(nodes,edges,minlink)
print("After trimming,",len(nodes),"nodes and",len(edges),"edges")

###
# Create networkx graph

Sgraph = nx.Graph()
Sgraph.add_nodes_from(nodes)
for i in range(0,len(edges)):
  node1,node2,myweight = edges[i]
  Sgraph.add_edge(node1,node2,weight=myweight)

print(nx.info(Sgraph))

###
# Louvain partitioning
import matplotlib.pyplot as plt
import matplotlib.cm as cm

Spartition = community_louvain.best_partition(Sgraph,weight='weight')
install_partitions(Sgraph,Spartition)

###
# Set up coloring based on ports

# Convert to graph_tool graph
from graph_tool.all import *

sgraph = nx2gt(Sgraph)

# Read in or create a layout
if layoutfilename is not None:
  layoutfile = open(layoutfilename,"rb")
  pos = pickle.load(layoutfile)
  layoutfile.close()
else:
  # note:  C is strength of repulsion, p is exponent of that
  # r is strength of attraction between connected
  # gamma is strength of repulsion between different groups, mu is exponent of that
  # K is optimal edge length
  C = 1000.0   # strength of repulsion
  p = 2.7  # exponent of C
  r = 0.1    # attraction between connected
  gamma = 6.0  # repulsion between groups
  mu = 3.0     # exponent of gamma
  
  pos = sfdp_layout(sgraph,eweight=sgraph.edge_properties["weight"],groups=sgraph.vertex_properties["mary_partition"],C=C,r=r,p=p,gamma=gamma,mu = mu)


outline_color = "k"      # outline nodes in black
# colors for Louvain clustering
printcolors = ["#608CFF","#E1A2FF","#FF83BF","#FF9B5C","#F8FB9F","#00FFA1","#46E0E3","#FFFFFF"]

# set up vertex properties
filldict,textdict,sizedict,port_to_fill = read_portcolors(name_to_num,num_to_port,colorfile)

sgraph.vertex_properties["mary_size"] = sgraph.new_vertex_property("int")
sgraph.vertex_properties["port_fill_color"] = sgraph.new_vertex_property("string")
sgraph.vertex_properties["partition_fill_color"] = sgraph.new_vertex_property("string")
sgraph.vertex_properties["mary_text_color"] = sgraph.new_vertex_property("string")

# set text color unconditionally (revise if this doesn't work well)
for vertex in sgraph.vertices():
  key = sgraph.vertex_properties["id"][vertex]
  sgraph.vertex_properties["mary_text_color"][vertex] = textdict[key]

# set node color by partition
for vertex in sgraph.vertices():
  key = sgraph.vertex_properties["id"][vertex]
  # color by transit port
  sgraph.vertex_properties["port_fill_color"][vertex] = filldict[key]
  # color by Louvain partition
  mypart = sgraph.vertex_properties["mary_partition"][vertex]
  sgraph.vertex_properties["partition_fill_color"][vertex] = printcolors[mypart]

# set node size conditionally (by year or outdegree)
for vertex in sgraph.vertices():
  key = sgraph.vertex_properties["id"][vertex]
  if year_size:
    # size by year
    sgraph.vertex_properties["mary_size"][vertex] = sizedict[key]
  else:
    # size by outdegree
    sgraph.vertex_properties["mary_size"][vertex] = vertex.out_degree()
# rescale sizes
sgraph.vertex_properties["mary_size"] = prop_to_size(sgraph.vertex_properties["mary_size"],mi=30.0,ma=70.0)

# set up edge properties

# set pen width for edges based on weight
sgraph.edge_properties["mary_pen_width"] = sgraph.new_edge_property("float")
sgraph.edge_properties["mary_pen_width"] = prop_to_size(sgraph.edge_properties["weight"],mi=-0.2,ma=10.0,power=0.4)

# set pen width to zero for edgeless graph
sgraph.edge_properties["mary_no_pen"] = sgraph.new_edge_property("float")
for edge in sgraph.edges():
  sgraph.edge_properties["mary_no_pen"][edge] = 0.0

# specify the arguments of the draw, to make it shorter and easier to debug
text = sgraph.vertex_properties["mary_nodename"]
port_color = sgraph.vertex_properties["port_fill_color"]
partition_color = sgraph.vertex_properties["partition_fill_color"]
text_color = sgraph.vertex_properties["mary_text_color"]
size = sgraph.vertex_properties["mary_size"]
pen = sgraph.edge_properties["mary_pen_width"]
no_pen = sgraph.edge_properties["mary_no_pen"]

# IMPORTANT NOTE about graph_tool:  the output type of graph_draw is a VertexPropertyMap
# giving vertex locations, UNLESS output = None (the default).  In that case it is a tuple
# of the same VertexPropertyMap and a map giving which notes were excluded!  So if you
# turn output on and off you get a different return type from the call.  This is super
# confusing.

# draw partition-colored graph with edges for hand adjustment; 2 value return 
pos, result = graph_draw(sgraph,pos=pos,vertex_text=text,vertex_fill_color=partition_color,output_size=(1000,1000),vertex_font_size=16,vertex_font_weight=cairo.FONT_WEIGHT_BOLD,edge_pen_width=pen,vertex_text_position=-2,vertex_text_color=text_color,vertex_size=size,vertex_color="k")

# write graph to file; 1 value return
pos = graph_draw(sgraph,pos=pos,vertex_text=text,vertex_fill_color=partition_color,output_size=(1000,1000),vertex_font_size=16,vertex_font_weight=cairo.FONT_WEIGHT_BOLD,edge_pen_width=pen,vertex_text_position=-2,vertex_text_color=text_color,vertex_size=size,vertex_color="k",output="network_graph_partition.svg")

new_layoutfilename = "new_layoutfile.pkl"
new_layoutfile = open(new_layoutfilename,"wb")
pickle.dump(pos,new_layoutfile)
new_layoutfile.close()

# write no-lines version to file; 1 value return
pos = graph_draw(sgraph,pos=pos,vertex_text=text,vertex_fill_color=partition_color,output_size=(1000,1000),vertex_font_size=16,vertex_font_weight=cairo.FONT_WEIGHT_BOLD,edge_pen_width=no_pen,vertex_text_position=-2,vertex_text_color=text_color,vertex_size=size,vertex_color="k",output="network_graph_partition_nolines.svg")

# write port-colored version to file; 1 value return
pos = graph_draw(sgraph,pos=pos,vertex_text=text,vertex_fill_color=port_color,output_size=(1000,1000),vertex_font_size=16,vertex_font_weight=cairo.FONT_WEIGHT_BOLD,edge_pen_width=pen,vertex_text_position=-2,vertex_text_color=text_color,vertex_size=size,vertex_color="k",output="network_graph_port.svg")

# write port-colored no-lines version to file; 1 value return
pos = graph_draw(sgraph,pos=pos,vertex_text=text,vertex_fill_color=port_color,output_size=(1000,1000),vertex_font_size=16,vertex_font_weight=cairo.FONT_WEIGHT_BOLD,edge_pen_width=no_pen,vertex_text_position=-2,vertex_text_color=text_color,vertex_size=size,vertex_color="k",output="network_graph_port_nolines.svg")

# make keys
seizurelist = []
used_ports = []
for vertex in sgraph.vertices():
  num = sgraph.vertex_properties["id"][vertex]
  seizurelist.append([int(num),num_to_name[num]])
  used_ports.append(num_to_port[num])
seizurelist.sort()
outfile = open("network_graph_key.tsv","w")
for entry in seizurelist:
  outline = [str(entry[0]),entry[1]]
  outline = "\t".join(outline) + "\n"
  outfile.write(outline)
outfile.close()

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
legenddata = []
for port,color in port_to_fill.items():
  if port in used_ports:
    entry = mpatches.Patch(color=color,label=port)
    legenddata.append(entry)
plt.legend(handles=legenddata)
plt.savefig("network_portkey.svg")

