import json

import networkx as nx


def create_networkx_graph(lif_file: str):
    with open(lif_file, "r") as f:
        lif_data = json.load(f)

    g = nx.Graph()
    for layout in lif_data["layouts"]:
        for node in layout["nodes"]:
            node_id = node["nodeId"]
            pos = node["nodePosition"]
            g.add_node(
                node_id,
                x=pos["x"],
                y=pos["y"],
            )
        for edge in layout["edges"]:
            start = edge["startNodeId"]
            end = edge["endNodeId"]
            g.add_edge(
                start, end,
                edgeId=edge["edgeId"],
            )
    return g