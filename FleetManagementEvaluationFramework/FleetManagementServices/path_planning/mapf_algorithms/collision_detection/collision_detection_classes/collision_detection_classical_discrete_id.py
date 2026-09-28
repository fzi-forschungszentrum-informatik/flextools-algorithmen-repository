import copy
from functools import partial

import numpy as np

from data.data_structures.extended_graph import ExtendedGraph
from interfaces.collision_detection_interface import CollisionDetectionInterface
from interfaces.decorators.override import override
from mapf_algorithms.collision_detection.detectors.collision_detection import detect_collision_earliest


def insert_constraints(conflict_node, collision, agent, index, constraint_id):
    conflict_node_new = copy.deepcopy(conflict_node)
    t1, t2, _, _, collision_kind = collision
    t = [t1, t2]
    if collision_kind == 'node':
        # Add node constraints
        conflict_node_new['constraints'].add((conflict_node['paths'][agent][t[index]], t[index]))
    else:  # Edge collision
        # Add edge constraints
        conflict_node_new['constraints'].add(((conflict_node['paths'][agent][t[index]],
                                               conflict_node['paths'][agent][t[index] + 1]), t[index]))
    return conflict_node_new


class CollisionDetectionClassicalDiscreteId(CollisionDetectionInterface):

    def __init__(self, exgraph: ExtendedGraph):
        super().__init__(exgraph)

    @override
    def get_empty_constraint_class(self):
        """
        :return: needed constraint structure/container
        """
        return set()

    @override
    def get_collision_detection_function(self):
        return detect_collision_earliest

    @override
    def get_insertion_function(self):
        """
        :return: needed function for inserting the constraint into the container
        """
        return partial(insert_constraints)

    @override
    def get_colliding_agents(self, collision):
        _, _, agent_1, agent_2, _ = collision
        return [agent_1, agent_2]

    @override
    def get_violates_constraints(self, constraints):
        return partial(self.violates_constraints, constraints=constraints)

    @override
    def get_has_infinite_interval(self, constraints):
        return partial(self.has_infinite_interval, constraints=constraints)

    def violates_constraints(self, location, timestamp, constraints):
        """
        :param constraints:
        :param location: an edge or node of a graph
        :param timestamp: point in time
        :return: checks if the given time interval intersects with any constraints on the given object, if so the
        constraint is violated
        """
        return (location, timestamp) in constraints

    def has_infinite_interval(self, location, constraints, start_time=1):
        """
        :param constraints:
        :param location: an edge or node of a graph
        :param start_time: a time point
        :return: checks if there is an infinite blocking interval that began earlier
        """
        return any(x == location and isinstance(y, tuple) and
                   y[0] <= start_time and y[1] == np.inf for x, y in constraints)
