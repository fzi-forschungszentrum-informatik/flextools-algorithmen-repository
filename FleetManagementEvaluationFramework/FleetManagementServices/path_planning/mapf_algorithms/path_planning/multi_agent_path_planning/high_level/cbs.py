import copy
import heapq
import itertools
from typing import List, Type
import logging
import numpy as np
import time

from config.config_file import MAX_TIME_CBS, LOGGER_NAME, MAX_GENERATED_NODES_CBS, CBS_COST_FUNCTION_IMPROVEMENT

from data.data_structures.extended_graph import ExtendedGraph
from interfaces.collision_detection_interface import CollisionDetectionInterface
from interfaces.low_level_search_interface import LowLevelSearchInterface
from interfaces.path_planning_heuristic_interface import Heuristic
from interfaces.path_planning_interface import PathPlanning
from mapf_algorithms.api_services.service_processing_functions import get_costs_for_path
from mapf_algorithms.collision_detection.constraints_structure.constraints3d import Constraints3D
from mapf_algorithms.heuristics.cost_functions import cbs_cost_function


logger = logging.getLogger(LOGGER_NAME)


class CBS(PathPlanning):

    def __init__(self, low_level_search: type[LowLevelSearchInterface],
                 collision_detection: Type[CollisionDetectionInterface]):
        self.a_star = low_level_search
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
        ################################################################################################################
        logger.debug(f'Start CBS computing path with {self.a_star.__name__}')
        number_of_agents = len(start_node_ids)
        logger.debug(f'CBS: Compute paths without collisions for {number_of_agents} Agents')
        logger.debug(f'With start locations: {start_node_ids}')
        logger.debug(f'And goal locations: {end_node_ids}')
        # meta data
        start_time = time.monotonic()
        elapsed = time.monotonic() - start_time
        generated_nodes_cbs = 1
        expanded_nodes_astar = 0
        ################################################################################################################
        collision_detection = self.collision_detection(graph)
        constraint_insertion_fct = collision_detection.get_insertion_function()
        collision_detection_fct = collision_detection.get_collision_detection_function()

        # build empty conflict tree root
        root = {
            'constraints': constraints,
            'paths': [],
            'costs': np.inf,
            'cost_paths': []
        }
        # get correct data format for constraints
        if root["constraints"] is None:
            root['constraints'] = collision_detection.get_empty_constraint_class()

        ################################################################################################################
        # computing initial paths for each AMR without collision constraints
        ################################################################################################################

        for i in range(number_of_agents):
            a_star = self.a_star(graph, layout_id, start_node_ids[i], end_node_ids[i], heuristic,
                                 vio_cons=collision_detection.get_violates_constraints(root['constraints']),
                                 has_inf=collision_detection.get_has_infinite_interval(root['constraints']))
            path, costs, add_expanded_nodes_astar = a_star.compute_path()
            expanded_nodes_astar += add_expanded_nodes_astar
            if path is None:
                # there exists no solution if no path is found without constraints
                logger.exception(f'No solvable path found with CBS, because of assumption error of MAPF')
                return None, None, generated_nodes_cbs, expanded_nodes_astar, None
            root['paths'].append(path)
            root['cost_paths'].append(get_costs_for_path(path))

        ################################################################################################################
        # adding the root node to the open list
        ################################################################################################################

        root['costs'] = cbs_cost_function(root['cost_paths'])
        open_list = []
        closed_list = set()

        heapq.heappush(open_list, copy.deepcopy((root['costs'], generated_nodes_cbs, root['paths'],
                                                 root['constraints'], root['cost_paths'])))

        solution_set = []

        ################################################################################################################
        # if the open list is not empty remove the CT-Node with the lowest cost from open list
        ################################################################################################################

        while (open_list and round(elapsed) < MAX_TIME_CBS and
               MAX_GENERATED_NODES_CBS >= generated_nodes_cbs):
            logger.debug(f'Open list CBS: {open_list}')
            # remove from open list
            costs, _id, paths, constraints, cost_paths = heapq.heappop(open_list)
            # recreate the node
            node = {
                'constraints': constraints,
                'paths': paths,
                'costs': costs,
                'cost_paths': cost_paths
            }
            ############################################################################################################
            # search for collisions in the current paths of the considered conflict node for all AMR
            ############################################################################################################

            collision = collision_detection_fct(node['paths'])
            # if no collision is found th node is optimal, before returning do some improvement
            if collision is None:
                if CBS_COST_FUNCTION_IMPROVEMENT is False:
                    logger.debug(
                        str('CBS found solution with paths ' + str(node['paths']) + ' and costs ' + str(
                            node['cost_paths'])))
                    return node['paths'], node['cost_paths'], generated_nodes_cbs, expanded_nodes_astar, node["constraints"]
                else:
                    logger.debug(str('CBS found possible solution with paths ' + str(node['paths']) + ' and costs ' +
                                     str(node['cost_paths'])))
                    heapq.heappush(solution_set, (node['costs'], node['paths'], node['constraints'],
                                                  node['cost_paths']))
                    logger.debug(f'Current solution set: {solution_set}')
                continue

            if len(solution_set) > 0:
                termination, open_list_element, generated_nodes_cbs = self.check_termination(open_list, solution_set,
                                                                                             generated_nodes_cbs,
                                                                                             collision_detection)
                if termination is True:
                    logger.info(f'Solution set: {solution_set}')
                    costs, _id, paths, constraints, cost_paths = heapq.heappop(solution_set)
                    logger.debug(f'CBS terminate with solution with paths {paths} and costs {cost_paths}')
                    return paths, cost_paths, generated_nodes_cbs, expanded_nodes_astar, constraints
                else:
                    heapq.heappush(open_list, open_list_element)

            ############################################################################################################
            # if a collisions found create two new nodes,
            # where one position is blocked for just one AMR that is colliding
            ############################################################################################################

            for a, agent in enumerate(collision_detection.get_colliding_agents(collision)):
                # Create two new conflict nodes
                new_node = constraint_insertion_fct(conflict_node=node,
                                                    collision=collision,
                                                    agent=agent,
                                                    index=a,
                                                    constraint_id=next(self.constraint_id))

                logger.debug(str(f'Compute path with A Star for agent {agent} with constraints:' +
                             str(new_node['constraints']) + ' from ' + start_node_ids[agent] + ' to ' +
                                 end_node_ids[agent]))
                ########################################################################################################
                # compute via a low level A* the new path the now blocked AMR will take
                ########################################################################################################
                a_star = self.a_star(graph, layout_id, start_node_ids[agent], end_node_ids[agent], heuristic,
                                     vio_cons=collision_detection.get_violates_constraints(new_node['constraints']),
                                     has_inf=collision_detection.get_has_infinite_interval(new_node['constraints']))

                new_path, costs, add_expanded_nodes_astar = a_star.compute_path()
                expanded_nodes_astar += add_expanded_nodes_astar
                logger.debug(f'New computed path: {new_path} with costs {costs}')
                ########################################################################################################
                # if there exists a path that could be taken add the node to the conflict tree
                ########################################################################################################
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
                    generated_nodes_cbs += 1
                    cbs_node = (new_node['costs'], generated_nodes_cbs, new_node['paths'], new_node['constraints'],
                                new_node['cost_paths'])
                    cbs_node = copy.deepcopy(cbs_node)
                    heapq.heappush(open_list, cbs_node)
            elapsed = time.monotonic()-start_time

        # Open list is empty or runtime is finished
        if len(solution_set) > 0:
            costs, _id, paths, constraints, cost_paths = heapq.heappop(solution_set)
            logger.info(f'Solution set: {solution_set}')
            logger.debug(f'CBS terminate because of empty open set or no more runtime'
                         f' with a solution with paths {paths} and costs {cost_paths}')
            return paths, cost_paths, generated_nodes_cbs, expanded_nodes_astar, constraints
        # Else, no solution found
        logger.info(f'No solvable path found with CBS in {MAX_TIME_CBS} seconds or max number generated nodes!')
        return None, None, generated_nodes_cbs, expanded_nodes_astar, None

    ####################################################################################################################
    ####################################################################################################################

    def check_termination(self, open_list, solution_set, node_counter, collision_detection):
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

