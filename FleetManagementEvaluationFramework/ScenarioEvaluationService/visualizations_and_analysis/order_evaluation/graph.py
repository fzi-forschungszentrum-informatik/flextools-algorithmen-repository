from collections import defaultdict, deque


class Graph(object):
    def __init__(self, nodes, init_graph):
        self.nodes = nodes
        self.graph = {}
        self.__construct_graph(nodes, init_graph)

    def __construct_graph(self, nodes, init_graph):
        """
        :param nodes: node id list
        :param init_graph: dictionary with connections of nodes
        :return: graph object
        """
        for node in nodes:
            self.graph[node] = {}

        self.graph.update(init_graph)
        # insert init_graph object to graph dictionary (connections), insert item from init graph to same key

        # For symmetrically graph
        for node, edges in self.graph.items():  # Iterate over all connection for all nodes in the graph
            for neighbor, costs in edges.items():  # Iterate over neighbor node with cost value
                if self.graph[neighbor].get(node, False) is False:
                    # If connection exists in both direction, if not than add the connection to the graph,
                    self.graph[neighbor][node] = costs

    def get_nodes(self):
        """
        :return: get all node ids of the graph object
        """
        return self.nodes

    def get_neighbors(self, node):
        """
        :param node: id string
        :return: get all neighbors of the node in the graph
        """
        connections = []
        for out_node in self.nodes:
            if self.graph[node].get(out_node, False) != False:
                connections.append(out_node)
        return connections

    def get_distance_between_nodes(self, node1, node2):
        """
        :param node1: string
        :param node2: string
        :return: returns the distance or cost between two nodes
        """
        return self.graph[node1][node2]

    def are_connected(self, node1, node2):
        """
        :param node1: node id, string
        :param node2: node id, string
        :return: boolean, if node1 and node2 are connected in the graph
        """
        visited = self.initialize_visited_list()
        return self.dfs(node1, node2, visited)

    def initialize_visited_list(self):
        visited = {node: False for node in self.graph}
        return visited

    def dfs(self, start_node, target_node, visited):
        """
        :param start_node: node id
        :param target_node: node id
        :param visited: List with information if start node visited
        :return: boolean, start node and target node connected
        :algorithm: recursive deep-first search algorithm, to check if nodes are connected
        """
        if start_node == target_node:
            return True

        visited[start_node] = True

        for neighbor in self.get_neighbors(start_node):
            if not visited[neighbor]:
                if self.dfs(neighbor, target_node, visited):
                    return True
        return False

    def remove_node(self, node):
        """
        :param node: node id
        :return: remove node from the graph
        """
        if node in self.nodes:
            self.nodes.remove(node)
        if node in self.graph:
            del self.graph[node]
        for nodes, edges in self.graph.items():
            if node in edges:
                del edges[node]
        return

    def bfs(self, start):
        dist = {}
        parents = defaultdict(list)
        queue = deque([start])
        dist[start] = 0
        while queue:
            u = queue.popleft()
            for v in self.get_neighbors(u):
                if v not in dist:
                    dist[v] = dist[u] + 1
                    parents[v].append(u)
                    queue.append(v)
                elif dist[v] == dist[u] + 1:
                    parents[v].append(u)

        return dist, parents

    def reconstruct_graph(self, parents, start, goal):
        all_paths = []
        path = []

        def dfs_rec(u):
            path.append(u)
            if u == start:
                all_paths.append(path[::-1])
            else:
                for p in parents[u]:
                    dfs_rec(p)
            path.pop()

        dfs_rec(goal)
        return all_paths