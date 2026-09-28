import copy
from functools import partial

import numpy as np
from intervaltree import IntervalTree, Interval

from data.data_structures.extended_graph import ExtendedGraph
from interfaces.collision_detection_interface import CollisionDetectionInterface
from interfaces.decorators.override import override
from mapf_algorithms.collision_detection.detectors.interval_collision_detection import detect_collision_on_interval_graph



def insert_interval_constraints(conflict_node, collision, agent, index, constraint_id, graph: ExtendedGraph):
    conflict_node_new = copy.deepcopy(conflict_node)
    block_start, block_end, _, _, collision_kind, col_point = collision
    if collision_kind == 'node':
        # Add node constraints
        if col_point not in conflict_node_new['constraints']:
            conflict_node_new['constraints'][col_point] = IntervalTree()
        conflict_node_new['constraints'][col_point].add(Interval(block_start, block_end + 0.001))
    else:  # Edge collision
        # Add edge constraints
        edge = graph.get_edge_id([col_point[0], col_point[1]])
        if edge not in conflict_node_new['constraints']:
            conflict_node_new['constraints'][edge] = IntervalTree()
        conflict_node_new['constraints'][edge].add(Interval(block_start, block_end + 0.001))
    return conflict_node_new


class CollisionDetectionClassicalIntervalsId(CollisionDetectionInterface):

    def __init__(self, exgraph: ExtendedGraph):
        super().__init__(exgraph)

    @override
    def get_empty_constraint_class(self):
        """
        :return: needed constraint structure/container
        """
        return dict()

    @override
    def get_collision_detection_function(self):
        return partial(detect_collision_on_interval_graph, exgraph=self.graph)

    @override
    def get_insertion_function(self):
        return partial(insert_interval_constraints, graph=self.graph)

    @override
    def get_colliding_agents(self, collision):
        _, _, agent_1, agent_2, _, _ = collision
        return [agent_1, agent_2]

    @override
    def get_block_start(self, collision):
        block_start, _, _, _, _, _ = collision
        return block_start

    @override
    def get_violates_constraints(self, constraints):
        return partial(self.violates_constraints, constraints=constraints)

    @override
    def get_has_infinite_interval(self, constraints):
        return partial(self.has_infinite_interval, constraints=constraints)

    def violates_constraints(self, location, interval, constraints):
        if location not in constraints:
            return False
        query_start, query_end = interval
        tree = constraints[location]
        overlaps = tree.overlap(query_start, query_end)
        return bool(overlaps)

    def has_infinite_interval(self, location, start_time=1, constraints=None):
        if location not in constraints:
            return False
        overlaps = constraints[location].overlap(0, np.inf)
        return any(iv.begin <= start_time and iv.end == np.inf for iv in overlaps)






