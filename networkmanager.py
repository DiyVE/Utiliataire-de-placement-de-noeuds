import networkx as nx
import matplotlib.pyplot as plt

def init_Graph():
    return nx.Graph()

def add_node_to_Graph(graph, node_id, x, y, description="", color='red', pref_angle="None"):
    graph.add_node(node_id, x=x, y=y, description=description, color=color, pref_angle=pref_angle)

def create_edges(graph, node_id):
    for node in graph.nodes():
        if node != node_id:
            graph.add_edge(node_id, node)
            
def get_nodes(graph):
    return graph.nodes(data=True)

def is_empty(graph):
    return graph.is_empty()
    
def read_node_props(graph, node_id):
    return graph.nodes[node_id]

def write_node_props(graph, node_id,**kwargs):
    for attrib, value in kwargs.items():
        if attrib in graph.nodes[node_id].keys():
            graph.nodes[node_id][attrib] = value
        else:
            raise KeyError("Node has no attribute {}".format(attrib))

def read_edges(graph, node_id):
    return graph.edges(node_id)

def delete_node(graph, node_id):
    graph.remove_node(node_id)

def number_of_edges(graph):
    return graph.number_of_edges()

def print_graph_debug(graph):
    nx.draw(graph, with_labels=True, font_weight='bold')
    plt.show()

def save_graph(graph, filename):
    nx.write_gml(graph, filename)

def read_graph(filename):
    return nx.read_gml(filename)