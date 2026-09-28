import itertools


import logging

import numpy as np


from config.config_file import LOGGER_NAME

from mapf_algorithms.collision_detection.bentley_ottmann.bo_collision_detector import BoDetector
from mapf_algorithms.collision_detection.bentley_ottmann.payload_data.payload_context import get_context
from data.data_structures.extended_graph import ExtendedGraph
from mapf_algorithms.collision_detection.collision_detection_help_functions import get_action_list, \
    get_detection_objects, create_flash_at_tau, get_positions_at_t, get_positions_at_t_constant_speed

from mapf_algorithms.collision_detection.solver import solve_for_constant_speeds, solve_for_varying_speeds


logger = logging.getLogger(LOGGER_NAME)

def bentley_ottmann_collision_detection_geometric(paths, exgraph: ExtendedGraph | None = None):
    """
    :param paths: list of paths of the amr, paths are lists and have the form (NodeID, (start, end)), nodes is a dict with all nodes and their characterizations
    -> each path looks something like this:
    -> [('A', (25.0, 26.1)), ('B', (40.0, 41.1)), ('D', (65.0, 66.1)), ('F', (95.0, 96.1)), ('E', (120.0, 121.1)), ('G', (135.0, 135.1)), ('I', (135.0, 135.1))]
    :param exgraph: graph object
    :return: collision time , agents, and collision kind, e.g. edge or node
    """
    ####################################################################################################################
    # Four Phases:
    # 1. Segmentation of the instance into time dependent intervals
    #    -> creation of the layout snapshots (flashes)
    # 2. Heuristic solving of snapshots until a collision is found
    # 3. Precise solving of the found collision to avoid false positives and to get precise collision intervals
    #    -> if false positive return to 2.
    # 4. If a precise collision was found handling of data and calculation of return values
    ####################################################################################################################
    # only one active Amr -> there will be no collisions
    if len(paths) <= 1:
        return None
    # gets ordered list of actions in the intervals
    action_list = get_action_list(paths)
    ####################################################################################################################
    # assures right data models for bentley ottmann version
    context = get_context()
    point, segment = context.point_cls, context.segment_cls
    ####################################################################################################################
    current = [0 for p in paths]        # remembers current position in path list
    current_nodes = dict()              # remembers current start and endpoints of the action interval
    current_action_interval = dict()    # remembers current interval on which the actions are performed
    for timestep in range(len(action_list)-1):
        ################################################################################################################
        # segments a bentley ottmann instance and save some data for next iterations and precise calculations
        segments, tau, current_nodes, current_action_interval, current =\
            create_flash_at_tau(paths, current, timestep, action_list, current_nodes, current_action_interval,
                                exgraph, point, segment)
        # initialise bentley ottmann detector, used as heuristic
        detector = BoDetector()
        ################################################################################################################
        # iterate through possible collisions, which are sets of amr
        for collision_set in detector.graph_get_collisions(segments):
            # if the set has more than one element investigate all pairs
            for amr1, amr2 in itertools.combinations(collision_set, 2):
                # instanciate collision objects which hold all necessary data for precise collision detection
                amr1_obj , amr2_obj = get_detection_objects(amr1, amr2, tau, current_action_interval,
                                                            current_nodes, exgraph)
                # solve equation -> if collision found handling of the collision data, else continue
                t1, t2, sp = solve_for_constant_speeds(amr1_obj,amr2_obj,)
                ########################################################################################################
                # Data handling
                if t1 is None and t2 is None:  # No collision was found
                    continue
                if t1 == -np.inf and t2 == np.inf: # special cases
                    if sp:
                        return tau, tau, amr1, amr2, "node", current_nodes[amr1][0] # the amr do not move on the same position
                    else:
                        continue  # amr move in same direction, without ever touching, solver gives -np.inf, np.inf back

                # [relt1, relt2] or [relt2, relt1] is the collision interval
                relt_1 = tau + t1
                relt_2 = tau + t2

                # if the collision interval is out of the interval in which the current action is executed search new collision
                # because the amr will change its action after the interval so there may not be a collision

                if((relt_1 <= current_action_interval[amr1][0] and relt_2 <= current_action_interval[amr1][0])
                    or (relt_1 >= current_action_interval[amr1][1] and relt_2 >= current_action_interval[amr1][1])
                    or (relt_1 <= current_action_interval[amr2][0] and relt_2 <= current_action_interval[amr2][0])
                    or (relt_1 >= current_action_interval[amr2][1] and relt_2 >= current_action_interval[amr2][1])):
                    continue

                if relt_1 != relt_2:
                    scol1, scol2 = get_positions_at_t_constant_speed(amr1_obj, amr2_obj, relt_1)
                    ecol1, ecol2 = get_positions_at_t_constant_speed(amr1_obj, amr2_obj, relt_2)
                    ################################################################################################
                    # return of ordered interval
                    return relt_1, relt_2, amr1, amr2, tuple(scol1), tuple(scol2), tuple(ecol1), tuple(ecol2)
                else:
                    ####################################################################################################
                    # if no other point was found return the first collision point
                    # verify make interval a little bigger ???
                    p1, p2 = get_positions_at_t_constant_speed(amr1_obj, amr2_obj, relt_1)
                    p3, p4 = get_positions_at_t_constant_speed(amr1_obj, amr2_obj, relt_2 + 0.2)
                    return relt_1, relt_2 + 0.2, amr1, amr2, tuple(p1), tuple(p2), tuple(p3), tuple(p4)
    # all timesteps ran through without finding any collisions there was None
    # this takes time at most:
    # n = number of active amr
    # k = number of possible collision
    # len(action_list) * ( ( n + k) * log_2(n)) + k * complexity of the solver (O(1))
    return None