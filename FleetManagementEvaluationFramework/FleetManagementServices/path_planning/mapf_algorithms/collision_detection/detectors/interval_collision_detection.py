import logging


from intervaltree import Interval, IntervalTree
from config.config_file import LOGGER_NAME
from data.data_structures.extended_graph import ExtendedGraph


logger = logging.getLogger(LOGGER_NAME)


def detect_collision_on_interval_graph(paths, exgraph: ExtendedGraph):
    id_graph = dict()
    collision = None
    for a, path in enumerate(paths):
        # add the intervals following the path, if a collision is found return collision
        for i, node in enumerate(path):
            if node[0] not in id_graph:
                # first insertion to graph structure - guaranteed to have no collision
                id_graph[node[0]] = IntervalTree()
                id_graph[node[0]].add(Interval(node[1][0], node[1][1], data=a))
            else:
                tree = id_graph[node[0]]
                overlaps = tree.overlap(node[1][0], node[1][1])
                if bool(overlaps):
                    # there is a collision
                    for interval in overlaps:
                        agent2 = interval.data
                        collision = node[1][0], node[1][1], a, agent2, "node", node[0]
                        break
                    if collision is not None:
                        return collision
                else:
                    id_graph[node[0]].add(Interval(node[1][0], node[1][1], data=a))
            if i+1 < len(path):
                edge_id = exgraph.get_edge_id([node[0], path[i+1][0]])
                edge_interval_start, edge_interval_end = node[1][1]-0.01, path[i+1][1][0]
                if edge_id not in id_graph:
                    # first insertion to graph structure - guaranteed to have no collision
                    id_graph[edge_id] = IntervalTree()
                    id_graph[edge_id].add(Interval(edge_interval_start, edge_interval_end, data=a))
                else:
                    tree = id_graph[edge_id]
                    overlaps = tree.overlap(edge_interval_start, edge_interval_end)
                    if bool(overlaps):
                        # there is a collision
                        for interval in overlaps:
                            agent2 = interval.data
                            collision = (edge_interval_start, edge_interval_end, a, agent2, "edge",
                                         (node[0], path[i+1][0]))
                            break
                        if collision is not None:
                            return collision
                    else:
                        id_graph[edge_id].add(Interval(edge_interval_start, edge_interval_end, data=a))
    return collision