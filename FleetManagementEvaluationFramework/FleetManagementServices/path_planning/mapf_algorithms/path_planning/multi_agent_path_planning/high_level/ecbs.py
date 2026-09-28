import copy
import itertools
from typing import List, Type
import logging
import numpy as np
import time
import heapq

from config.config_file import MAX_TIME_CBS, LOGGER_NAME
import config.config_file
from interfaces.collision_detection_interface import CollisionDetectionInterface
from interfaces.low_level_search_interface import LowLevelSearchInterface
from interfaces.path_planning_heuristic_interface import Heuristic
from interfaces.path_planning_interface import PathPlanning

from data.data_structures.extended_graph import ExtendedGraph
from mapf_algorithms.api_services.service_processing_functions import get_costs_for_path
from mapf_algorithms.collision_detection.constraints_structure.constraints3d import Constraints3D
from mapf_algorithms.heuristics.cost_functions import cbs_cost_function

from mapf_algorithms.path_planning.multi_agent_path_planning.low_level.a_star import AStar

from mapf_algorithms.path_planning.multi_agent_path_planning.low_level.focal_search import FocalSearch

logger = logging.getLogger(LOGGER_NAME)


class ECBS(PathPlanning):

    def __init__(self, w, focal_heuristic, low_level_search: type[LowLevelSearchInterface],
                 collision_detection: Type[CollisionDetectionInterface]):
        self.w_low = w
        self.w_high = w
        self.focal_heuristic = focal_heuristic
        self.open_list = []
        self.focal_list = []
        self.current_f_min_value = np.inf
        self.focal_search = low_level_search
        self.collision_detection: Type[CollisionDetectionInterface] = collision_detection
        self.constraint_id = itertools.count()

    def path_planning(self, graph: ExtendedGraph, layout_id: str, start_node_ids: List[str], end_node_ids: List[str],
                      constraints, tokens, heuristic: Heuristic):
        """
        :param graph: extended graph object
        :param layout_id: layout identification
        :param start_node_ids: start node list
        :param end_node_ids: end node list
        :param constraints: at the moment not needed initially
        :param tokens: not needed
        :param heuristic: heuristic interface to compute the heuristic distance to the goal, e.g. manhattan distance
        :return: [paths], [costs of paths]
        :algorithm: conflict-based-search
        """
        ##############################################################################################
        # important data structures
        self.open_list = []
        self.focal_list = []
        closed_list = set()
        self.current_f_min_value = np.inf
        # logging
        logger.info(f'Start ECBS computing path with {self.focal_search.__name__}')
        number_of_agents = len(start_node_ids)
        logger.debug(f'ECBS: Compute paths without collisions for {number_of_agents} Agents')
        logger.debug(f'With start locations: {start_node_ids}')
        logger.debug(f'And goal locations: {end_node_ids}')
        # meta data
        start_time = time.monotonic()
        elapsed = time.monotonic() - start_time
        generated_nodes_ecbs = 1
        expanded_nodes_astar = 0
        ##############################################################################################

        collision_detection = self.collision_detection(graph)
        collision_detection_fct = collision_detection.get_collision_detection_function()
        constraint_insertion_fct = collision_detection.get_insertion_function()

        # build empty CBS Tree root
        root = {
            'constraints': constraints,
            'paths': [],
            'costs': np.inf,
            'cost_paths': []
        }
        # get correct data format for constraints
        if root["constraints"] is None:
            root['constraints'] = collision_detection.get_empty_constraint_class()

        ###############################################################################
        # calculating initial paths for each AMR without collision constraints
        ###############################################################################

        for i in range(number_of_agents):
            focal_astar = self.focal_search(graph, layout_id, start_node_ids[i], end_node_ids[i], heuristic,
                                            vio_cons=collision_detection.get_violates_constraints(root['constraints']),
                                            has_inf=collision_detection.get_has_infinite_interval(root['constraints']))
            focal_astar.init_focal(self.w_low, self.focal_heuristic, root['paths'])
            path, costs, add_expanded_nodes = focal_astar.compute_path()
            expanded_nodes_astar += add_expanded_nodes
            if path is None:
                # there exists no solution if no path is found without constraints
                logger.exception(f'No solvable path found with ECBS, because of assumption error of MAPF')
                return None, None, generated_nodes_ecbs, expanded_nodes_astar, None
            root['paths'].append(path)
            root['cost_paths'].append(get_costs_for_path(path))

        ############################################################
        # adding the root node to the open list
        ############################################################

        root['costs'] = cbs_cost_function(root['cost_paths'])
        heapq.heappush(self.open_list, (root['costs'], generated_nodes_ecbs, root['paths'], root['constraints'],
                                        root['cost_paths']))
        ###########################################################################################################
        # update focal list such that
        # all CT nodes of the open list with cost lower than (the minimal cost in the open list * w)are in there
        ###########################################################################################################

        self.update_focal_list()
        solution_set = []
        ################################################################################################
        # if the open list is not empty remove the CT-Node with the lowest cost from focal list
        ################################################################################################
        while (self.open_list and round(elapsed) < MAX_TIME_CBS and
               config.config_file.MAX_GENERATED_NODES_CBS >= generated_nodes_ecbs):

            logger.debug(f'Open list ECBS: {self.open_list}')
            # remove from focal list
            focal_costs, _id, costs, paths, constraints, cost_paths = heapq.heappop(self.focal_list)
            # remove duplicate from open-list
            self.open_list.remove((costs, _id, paths, constraints, cost_paths))
            # if the minimum value of the open list did change update the focal list
            if len(self.open_list) > 0:
                if self.open_list[0][0] > self.current_f_min_value:
                    # take minimal value and update with it
                    self.current_f_min_value = self.open_list[0][0]
                    self.update_focal_list()
            # recreate the node
            node = {
                'constraints': constraints,
                'paths': paths,
                'costs': costs,
                'cost_paths': cost_paths,
                'focal_costs': focal_costs
            }
            ###############################################################
            # search for collisions in the current paths for all AMR
            ###############################################################

            collision = collision_detection_fct(node['paths'])

            # if no collision is found th node is optimal, before returning do some improvement
            if collision is None:
                if config.config_file.CBS_COST_FUNCTION_IMPROVEMENT is False:
                    logger.debug(
                        str('CBS found solution with paths ' + str(node['paths']) + ' and costs ' + str(
                            node['cost_paths'])))
                    return node['paths'], node['cost_paths'], generated_nodes_ecbs, expanded_nodes_astar, node["constraints"]
                else:
                    logger.debug(str('CBS found possible solution with paths ' + str(node['paths']) + ' and costs ' +
                                     str(node['cost_paths'])))
                    heapq.heappush(solution_set, (node['costs'], node['paths'], node['constraints'],
                                                  node['cost_paths']))
                    logger.debug(f'Current solution set: {solution_set}')
                continue

            if len(solution_set) > 0:
                termination, open_list_element, node_counter = self.check_termination(self.open_list, solution_set,
                                                                                      generated_nodes_ecbs,
                                                                                      collision_detection)
                if termination is True:
                    logger.info(f'Solution set: {solution_set}')
                    costs, paths, constraints, cost_paths = heapq.heappop(solution_set)
                    logger.debug(f'CBS terminate with solution with paths {paths} and costs {cost_paths}')
                    return paths, cost_paths, generated_nodes_ecbs, expanded_nodes_astar, constraints
                else:
                    heapq.heappush(self.open_list, open_list_element)

            for a, agent in enumerate(collision_detection.get_colliding_agents(collision)):
                # Create two new nodes
                new_node = constraint_insertion_fct(conflict_node=node,
                                                    collision=collision,
                                                    agent=agent,
                                                    index=a,
                                                    constraint_id=next(self.constraint_id))

                logger.debug(str(f'Compute path with A Star for agent {agent} with constraints:' +
                                 str(new_node['constraints']) + ' from ' + start_node_ids[agent] + ' to ' +
                                 end_node_ids[agent]))

                ############################################################################################
                # compute via a low level focal search the new path the now blocked AMR will take
                ############################################################################################

                focal_astar = self.focal_search(graph, layout_id, start_node_ids[agent], end_node_ids[agent],
                                                heuristic,
                                                vio_cons=collision_detection.get_violates_constraints(
                                                    new_node['constraints']),
                                                has_inf=collision_detection.get_has_infinite_interval(
                                                    new_node['constraints'])
                                                )
                other_paths = node['paths'][:agent] + node['paths'][agent+1:]
                focal_astar.init_focal(self.w_low, self.focal_heuristic, other_paths)

                new_path, costs, add_expanded_nodes = focal_astar.compute_path()
                expanded_nodes_astar += add_expanded_nodes

                logger.debug(f'New computed path: {new_path} with costs {costs}')
                ##############################################################################
                # if there exists a path that could be taken add the node to the conflict tree
                ##############################################################################
                if new_path is not None:
                    new_node['paths'][agent] = new_path
                    new_node['cost_paths'][agent] = get_costs_for_path(new_path)  # costs depending on cost function
                    new_node['costs'] = cbs_cost_function(new_node['cost_paths'])
                    if not isinstance(node["constraints"], Constraints3D):
                        constraints_key = (
                            frozenset(new_node['constraints']),
                            hash(str(new_node['paths']))
                        )
                        if constraints_key not in closed_list:
                            closed_list.add(constraints_key)
                        else:
                            continue
                    generated_nodes_ecbs += 1
                    cbs_node = (new_node['costs'], generated_nodes_ecbs, new_node['paths'], new_node['constraints'],
                                new_node['cost_paths'])

                    # push the new node into the high level focal search representing the CT
                    heapq.heappush(self.open_list, cbs_node)
                    if new_node['costs'] < self.current_f_min_value:
                        self.current_f_min_value = new_node['costs']
                        self.update_focal_list()

            elapsed = time.monotonic()-start_time

            if len(self.focal_list) == 0 and len(self.open_list) > 0:
                self.current_f_min_value = self.open_list[0][0]
                self.update_focal_list()

        ##################################################
        # Open list is empty or runtime is finished
        ##################################################

        if len(solution_set) > 0:
            costs, _id, paths, constraints, cost_paths = heapq.heappop(solution_set)
            logger.info(f'Solution set: {solution_set}')
            logger.debug(f'CBS terminate because of empty open set or no more runtime'
                         f' with a solution with paths {paths} and costs {cost_paths}')
            return paths, cost_paths, generated_nodes_ecbs, expanded_nodes_astar, constraints
        # Else, no solution found
        logger.info(f'No solvable path found with ECBS in {MAX_TIME_CBS} seconds or max number generated nodes!')

        return None, None, generated_nodes_ecbs, expanded_nodes_astar, None
    ####################################################################################################################
    ####################################################################################################################

    def check_termination(self, open_list, solution_set, node_counter, collision_detection):
        # (root['costs'], root['paths'], root['constraints'], root['cost_paths'])
        number_agents = len(solution_set[0][1])
        paths_new_open_list_element = []
        termination = True
        for i in range(number_agents):
            min_path_solution_costs = np.inf
            path_solution = None
            for solution in solution_set:
                if solution[3][i] < min_path_solution_costs:
                    min_path_solution_costs = solution[3][i]
                    path_solution = solution[1][i]
            min_path_open_list_costs = np.inf
            path_open = None
            for item in open_list:
                if item[3][i] < min_path_open_list_costs:
                    min_path_open_list_costs = item[3][i]
                    path_open = item[1][i]
            if min_path_open_list_costs < min_path_solution_costs:
                paths_new_open_list_element.append(path_open)
                termination = False
            else:
                paths_new_open_list_element.append(path_solution)
        costs_paths = []
        for path in paths_new_open_list_element:
            costs_paths.append(get_costs_for_path(path))
        costs = cbs_cost_function(costs_paths)
        node_counter += 1
        open_list_element = (costs, node_counter, paths_new_open_list_element,
                             collision_detection.get_empty_constraint_class(), costs_paths)
        return termination, open_list_element, node_counter

    def update_focal_list(self):
        self.focal_list = []
        bound = self.w_high * self.current_f_min_value
        # elem := (costs, tiebreaker, paths, constraints, cost_paths)
        for elem in self.open_list:
            if elem[0] <= bound:
                heapq.heappush(self.focal_list, (self.focal_heuristic(elem[2]),
                                                               elem[1], elem[0], elem[2], elem[3], elem[4]))
        return
