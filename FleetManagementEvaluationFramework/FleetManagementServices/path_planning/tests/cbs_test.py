from data.data_structures.extended_graph import ExtendedGraph
from data.data_structures.graph import Graph

def test_cbs(monkeypatch):
    graph = {}
    init_graph = {}
    nodes = []
    for edge in ['ab', 'ac', 'cd', 'bd', 'de']:
        if edge[0] not in nodes:
            nodes.append(edge[0])
            init_graph[edge[0]] = {}
        if edge[1] not in nodes:
            nodes.append(edge[1])
            init_graph[edge[1]] = {}

        init_graph[edge[0]][edge[1]] = 1
        init_graph[edge[1]][edge[0]] = 1

    for node in nodes:
        init_graph[node][node] = 0

    graph['g1'] = Graph(nodes, init_graph)

    graph = {}
    init_graph = {}
    nodes = []
    for edge in ['ab', 'be', 'ad', 'cd', 'de', 'df', 'fi', 'gh', 'hi', 'ij']:
        if edge[0] not in nodes:
            nodes.append(edge[0])
            init_graph[edge[0]] = {}
        if edge[1] not in nodes:
            nodes.append(edge[1])
            init_graph[edge[1]] = {}

        init_graph[edge[0]][edge[1]] = 1
        init_graph[edge[1]][edge[0]] = 1

    for node in nodes:
        init_graph[node][node] = 0

    graph['g2'] = ExtendedGraph(nodes, init_graph, nodes_lif=[], edges_lif=[], stations_lif=[])

