import copy
from functools import partial


import numpy as np
import config.config_file

from data.data_structures.extended_graph import ExtendedGraph
from interfaces.collision_detection_interface import CollisionDetectionInterface
from interfaces.decorators.override import override
from mapf_algorithms.collision_detection.constraints_structure.constraints3d import Constraints3D
from mapf_algorithms.collision_detection.detectors.bentley_ottmann_geometric import \
    bentley_ottmann_collision_detection_geometric


def insert_zone_constraint(conflict_node, collision, agent, index, constraint_id):
    conflict_node_new = copy.deepcopy(conflict_node)

    block_start, block_end, agent_1, agent_2, a1_spos, a2_spos, a1_epos, a2_epos = collision
    agents_starts = [a1_spos, a2_spos]
    agents_ends = [a1_epos, a2_epos]
    agents_block_ends = [block_end, block_end]

    zones = {}

    if conflict_node["paths"][agent][-1][1][0] <= block_start:
        agents_block_ends[index] = np.inf  # mark the block as infinite since the agent won't move anymore
    if conflict_node_new["constraints"] is None:
        conflict_node_new['constraints'] = Constraints3D()

    zones[index] = conflict_node_new["constraints"].get_new_zone(start=agents_starts[(index + 1) % 2],
                                                                 end=agents_ends[(index + 1) % 2],
                                                                 radius=config.config_file.AMR_RADIUS,
                                                                 t_start=block_start,
                                                                 t_end=agents_block_ends[(index + 1) % 2])

    conflict_node_new["constraints"].insert_zone(zone_id=constraint_id, zone=zones[index])

    return conflict_node_new


class CollisionDetectionPrecheckingIntervalsGeometricPartial(CollisionDetectionInterface):

    def __init__(self, exgraph: ExtendedGraph):
        super().__init__(exgraph)

    @override
    def get_empty_constraint_class(self):
        """
        :return: needed constraint structure/container
        """
        return Constraints3D()

    @override
    def get_collision_detection_function(self):
        """
        :return: needed collision detection
        """
        return partial(bentley_ottmann_collision_detection_geometric, exgraph=self.graph)  # Constant speed profile

    # @override
    # def get_constraint_function(self):
    #     """
    #     :return: return function needed for creating the correct constraint format
    #     """
    #     return create_blocking_zones

    @override
    def get_insertion_function(self):
        """
        :return: function needed for inserting the zone into the constraint
        """
        return partial(insert_zone_constraint)

    @override
    def get_block_start(self, collision):
        block_start, _, _, _, _, _, _, _ = collision
        return block_start

    @override
    def get_colliding_agents(self, collision):
        _, _, agent_1, agent_2, _, _, _, _ = collision
        return [agent_1, agent_2]

    def get_violates_constraints(self, constraints):
        return partial(self.violates_constraints, constraints = constraints)

    def get_has_infinite_interval(self, constraints):
        return partial(self.has_infinite_interval, constraints = constraints)

    def violates_constraints(self, location, interval, constraints):
        """
        :param constraints:
        :param location: an edge or node of a graph
        :param interval: a time interval
        :return: checks if the given time interval intersects with any constraints on the given object, if so the
        constraint is violated
        """
        if constraints is None:
            return False

        ps, pe, rad = self.extract_data(location)

        query_start, query_end = interval

        if not pe == ps or query_start == query_end-0.1:
            violation, _ = constraints.query_circle(ps, rad, query_start)
            return violation
        else:

            zone = constraints.get_new_zone(ps, pe, rad, query_start, query_end)

            violation, _ = constraints.query_obb(zone, query_start, query_end)
            return violation

    def extract_data(self, location_id: str):
        if location_id in self.graph.nodes_obj.keys():
            location = self.graph.nodes_obj[location_id]
            position_start = (location.nodePosition.x, location.nodePosition.y)
            return position_start, position_start, config.config_file.AMR_RADIUS
        elif location_id in self.graph.edges_obj.keys():
            location = self.graph.edges_obj[location_id]
            position_start = (self.graph.nodes_obj[location.startNodeId].nodePosition.x,
                              self.graph.nodes_obj[location.startNodeId].nodePosition.y)
            position_end = (self.graph.nodes_obj[location.endNodeId].nodePosition.x,
                              self.graph.nodes_obj[location.endNodeId].nodePosition.y)
            return position_start, position_end, config.config_file.AMR_RADIUS
        else:
            return None, None, None

    def has_infinite_interval(self, location, start_time, constraints):
        return self.violates_constraints(location, (start_time, np.inf), constraints)
