import math
import os

import networkx as nx
import pandas as pd


def compute_graph_properties(graph: nx.Graph, name: str, distance: float, layout: str, pos):
    file_name_graph_properties = rf'./graph_properties/{layout}_graph_properties.csv'

    if file_name_graph_properties is not None:
        os.makedirs("./graph_properties", exist_ok=True)

    for n in graph.nodes:
        graph.nodes[n]['x'], graph.nodes[n]['y'] = pos[n]

    for u, v in graph.edges():
        graph[u][v]['weight'] = euclidean(u, v, graph)

    degrees = dict(graph.degree())
    mean_degree = sum(degrees.values()) / graph.number_of_nodes()

    deg_centrality = nx.degree_centrality(graph)
    avg_deg_centrality = sum(deg_centrality.values()) / len(deg_centrality)

    if isinstance(graph, nx.DiGraph):
        bet_centrality = nx.betweenness_centrality(graph.to_undirected())
        close_centrality = nx.closeness_centrality(graph.to_undirected())
        clustering = nx.average_clustering(graph.to_undirected())
    else:
        bet_centrality = nx.betweenness_centrality(graph)
        close_centrality = nx.closeness_centrality(graph)
        clustering = nx.average_clustering(graph)
    
    avg_bet_centrality = sum(bet_centrality.values()) / len(bet_centrality)
    avg_close_centrality = sum(close_centrality.values()) / len(close_centrality)

    if isinstance(graph, nx.DiGraph):
        num_components = len(list(nx.weakly_connected_components(graph)))
    else:
        num_components = len(list(nx.connected_components(graph)))

    df = pd.DataFrame({
        "Graph": [name],
        "Number of nodes": [graph.number_of_nodes()],
        "Number of edges": [graph.number_of_edges()],
        "Edge distance": [distance],
        "Density": [nx.density(graph)],
        "Mean degree": [mean_degree],
        "Number of components": [num_components],
        "degree_centrality": [avg_deg_centrality],
        "bet_centrality": [avg_bet_centrality],
        "close_centrality": [avg_close_centrality],
        "clustering": [clustering],
        "diameter": [weighted_diameter(graph)],
        "Avg. shortest path length": [nx.average_shortest_path_length(graph.to_undirected() if isinstance(graph, nx.DiGraph) else graph, weight='weight')],
    })
    file_exists = os.path.exists(file_name_graph_properties)
    df.to_csv(
        file_name_graph_properties,
        mode='a' if file_exists else 'w',
        header=not file_exists,
        index=False,
        sep=';',
        decimal=','
    )
    return


def euclidean(u, v, graph):
    x1, y1 = graph.nodes[u]['x'], graph.nodes[u]['y']
    x2, y2 = graph.nodes[v]['x'], graph.nodes[v]['y']
    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)


def weighted_diameter(graph):
    if isinstance(graph, nx.DiGraph):
        graph = graph.to_undirected()
    
    lengths = dict(nx.all_pairs_dijkstra_path_length(graph, weight='weight'))
    return max(max(d.values()) for d in lengths.values())
