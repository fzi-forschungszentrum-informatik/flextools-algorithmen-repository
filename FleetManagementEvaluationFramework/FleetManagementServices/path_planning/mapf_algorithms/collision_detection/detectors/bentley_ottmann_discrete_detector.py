import logging

from config.config_file import LOGGER_NAME

from mapf_algorithms.collision_detection.bentley_ottmann.bo_collision_detector import BoDetector
from mapf_algorithms.collision_detection.bentley_ottmann.payload_data.payload_context import get_context
from data.data_structures.extended_graph import ExtendedGraph


logger = logging.getLogger(LOGGER_NAME)


def bentley_ottmann_collision_detection_evenly_spaced_times(paths, exgraph: ExtendedGraph):
    """
    :param paths: list of paths of the amr, paths are lists and have the form (NodeID), nodes is a dict
     with all nodes and their characterizations
     :param exgraph: graph object
    :return: collision time, agents, and collision kind, e.g. edge or node
    """

    nodes = exgraph.nodes_obj

    context = get_context()
    point, segment = context.point_cls, context.segment_cls
    times = [len(x) for x in paths]  # max len of path, since every node is a timestep
    for timestep in range(max(times)-1):
        segments = []
        for amr in range(len(paths)):
            if times[amr] > timestep + 1:
                snode = paths[amr][timestep]
                enode = paths[amr][timestep+1]
            else:
                snode = paths[amr][times[amr]-1]
                enode = paths[amr][times[amr]-1]

            start = point(nodes[snode].nodePosition.x, nodes[snode].nodePosition.y)
            end = point(nodes[enode].nodePosition.x, nodes[enode].nodePosition.y)

            if not start.__eq__(end):
                segments.append(segment(start, end, {amr}))
            else:
                start = point(nodes[snode].nodePosition.x-0.005, nodes[snode].nodePosition.y-0.5)
                end = point(nodes[enode].nodePosition.x+0.005, nodes[enode].nodePosition.y+0.5)
                segments.append(segment(start, end, {amr}))

        ret = BoDetector().graph_get_collision(segments)
        if ret is not None:
            amr1, amr2 = ret
            l1 = min(len(paths[amr1])-1, timestep)
            r1 = min(len(paths[amr1])-1, timestep+1)
            l2 = min(len(paths[amr2])-1, timestep)
            r2 = min(len(paths[amr2])-1, timestep+1)


            if (paths[amr1][r1] == paths[amr2][r2]):
                if paths[amr1][l1] == paths[amr2][l2]:
                    # both amr drive on the same edges, collision already on the first node, no edge collision
                    return l1, l2, amr1, amr2, "node"
                else:
                    #collision on the end node of both amr
                    return r1, r2, amr1, amr2, 'node'
            elif (paths[amr1][l1] == paths[amr2][r2]):
                # amr drive on the same edge but in opposite directions and will collide
                if (paths[amr1][r1] == paths[amr2][l2]):
                    return (l1, l2, amr1, amr2, "node" if paths[amr1][l1] == paths[amr1][r1] or
                                                          paths[amr2][l2] == paths[amr2][r2] else "edge") # could also return r1, r2
                else:
                    continue # l1, r2, amr1, amr2, "node" ?
            elif (paths[amr1][r1] == paths[amr2][l2]):
                # amr drive on the same edge but in opposite directions and will collide, but directions are swapped
                if paths[amr1][l1] == paths[amr2][r2]:
                    return (l1, l2, amr1, amr2, "node" if paths[amr1][l1] == paths[amr1][r1] or
                                                          paths[amr2][l2] == paths[amr2][r2] else "edge")    # could also return r1, r2
                else:
                    continue # r1, l2, amr1, amr2, "node" ?
            elif (paths[amr1][l1] == paths[amr2][l2]):
                # amr collide on their start nodes
                return l1, l2, amr1, amr2, "node"
    return None