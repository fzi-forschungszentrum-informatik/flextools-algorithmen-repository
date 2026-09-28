import networkx as nx


def create_graph(odrm_graph, odrm_positions):
    udrm = nx.Graph()
    
    for node_id in odrm_graph.nodes():
        if node_id < len(odrm_positions):
            udrm.add_node(node_id, pos=odrm_positions[node_id])
        else:
            udrm.add_node(node_id)
    
    for u, v in odrm_graph.edges():
        if not udrm.has_edge(u, v):
            udrm.add_edge(u, v)
    
    return udrm
