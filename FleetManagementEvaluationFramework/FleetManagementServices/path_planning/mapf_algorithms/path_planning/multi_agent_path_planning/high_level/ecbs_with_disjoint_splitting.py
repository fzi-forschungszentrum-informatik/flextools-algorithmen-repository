import copy
from typing import List, Type
import logging
import numpy as np
import time
import heapq

from config.config_file import MAX_TIME_CBS, LOGGER_NAME
import config.config_file
from interfaces.low_level_search_interface import LowLevelSearchInterface
from interfaces.path_planning_heuristic_interface import Heuristic
from interfaces.path_planning_interface import PathPlanning

from data.data_structures.extended_graph import ExtendedGraph
from mapf_algorithms.api_services.service_processing_functions import get_costs_for_path
from mapf_algorithms.collision_detection.detectors.collision_detection import detect_collision_earliest
from mapf_algorithms.heuristics.cost_functions import cbs_cost_function


logger = logging.getLogger(LOGGER_NAME)


class ECBSDisjointSplitting(PathPlanning):

    def __init__(self, low_level_search: Type[LowLevelSearchInterface], w, focal_heuristic):
        self.focal_search = low_level_search
        self.w_low = w
        self.w_high = w
        self.focal_heuristic = focal_heuristic
        self.open_list = []
        self.focal_list = []
        self.current_f_min_value = np.inf

    def path_planning(self, graph: ExtendedGraph, layout_id: str, start_node_ids: List[str], end_node_ids: List[str],
                      constraints, tokens, heuristic: Heuristic):
        """
        :param graph: graph object
        :param layout_id: layout identification
        :param start_node_ids: start node list
        :param end_node_ids: end node list
        :param constraints: at the moment not needed initially
        :param tokens: not needed
        :param heuristic: heuristic interface to compute the heuristic distance to the goal, e.g. manhattan distance
        :return: [paths], [costs of paths]
        :algorithm: conflict-based-search
        """
        self.open_list = []
        self.focal_list = []
        closed_list = set()
        self.current_f_min_value = np.inf
        self.closed_list = set()

        logger.info('Start ECBS with Disjoint Splitting computing path')
        number_of_agents = len(start_node_ids)
        logger.debug(f'ECBS: Compute paths without collisions for {number_of_agents} Agents')
        logger.debug(f'With start locations: {start_node_ids}')
        logger.debug(f'And goal locations: {end_node_ids}')

        start_time = time.monotonic()
        elapsed = time.monotonic() - start_time
        generated_nodes_ecbs = 1
        expanded_nodes_astar = 0

        if constraints is None:
            constraints = set()

        root = {
            'neg_constraints': constraints,
            'pos_constraints': set(),
            'paths': [],
            'costs': np.inf,
            'cost_paths': []
        }

        ################################################################################################################
        # calculating initial paths for each AMR without collision constraints
        for i in range(number_of_agents):
            focal_search = self.focal_search(graph, layout_id, start_node_ids[i], end_node_ids[i],
                                       root['neg_constraints'], heuristic, i)
            focal_search.init_focal(self.w_low, self.focal_heuristic, root['paths'])
            path, costs, add_expanded_nodes_astar = focal_search.compute_path()
            expanded_nodes_astar += add_expanded_nodes_astar
            if path is None:
                # there exists no solution if no path is found without constraints
                logger.exception(f'No solvable path found with ECBS, because of assumption error of MAPF')
                return None, None, generated_nodes_ecbs, expanded_nodes_astar, None
            root['paths'].append(path)
            root['cost_paths'].append(get_costs_for_path(path))
        ################################################################################################################
        # adding the root node to the open list
        root['costs'] = cbs_cost_function(root['cost_paths'])
        heapq.heappush(self.open_list, (root['costs'], generated_nodes_ecbs, root['paths'],
                                        root['neg_constraints'], root['pos_constraints'], root['cost_paths']))
        ################################################################################################################
        # update focal list such that
        # all CT nodes of the open list with cost lower than (the minimal cost in the open list * w)are in there
        self.update_focal_list()
        solution_set = []

        ################################################################################################################
        # if the open list is not empty remove the CT-Node with the lowest cost from focal list
        while (self.open_list and round(elapsed) < MAX_TIME_CBS and
               config.config_file.MAX_GENERATED_NODES_CBS >= generated_nodes_ecbs):
            logger.debug(f'Open list ECBS: {self.open_list}')
            # remove from focal list
            focal_costs, _id, costs, paths, neg_constraints, pos_constraints, cost_paths = heapq.heappop(self.focal_list)
            # remove duplicate from open-list
            self.open_list.remove((costs, _id, paths, neg_constraints, pos_constraints, cost_paths))
            # if the minimum value of the open list did change update the focal list
            if len(self.open_list) > 0:
                if self.open_list[0][0] > self.current_f_min_value:
                    # take minimal value and update with it
                    self.current_f_min_value = self.open_list[0][0]
                    self.update_focal_list()
            # recreate the node
            node = {
                'neg_constraints': neg_constraints,
                'pos_constraints': pos_constraints,
                'paths': paths,
                'costs': costs,
                'cost_paths': cost_paths,
                'focal_costs': focal_costs
            }
            ############################################################################################################
            # search for collisions in the current paths for all AMR
            collision = detect_collision_earliest(node['paths'])

            # if no collision is found th node is optimal, before returning do some improvement
            if collision is None:
                if config.config_file.CBS_COST_FUNCTION_IMPROVEMENT is False:
                    logger.debug(
                        str('CBS found solution with paths ' + str(node['paths']) + ' and costs ' + str(
                            node['cost_paths'])))
                    return node['paths'], node['cost_paths'], generated_nodes_ecbs, expanded_nodes_astar, node["neg_constraints"] # Collision free solution found
                else:
                    logger.debug(str('CBS found possible solution with paths ' + str(node['paths']) + ' and costs ' +
                                     str(node['cost_paths'])))
                    heapq.heappush(solution_set, (node['costs'], node['paths'], node['constraints'],
                                                  node['cost_paths']))
                    logger.debug(f'Current solution set: {solution_set}')
                continue

            if len(solution_set) > 0:
                termination, open_list_element, node_counter = self.check_termination(self.open_list, solution_set, generated_nodes_ecbs)
                if termination is True:
                    logger.info(f'Solution set: {solution_set}')
                    costs, paths, constraints, cost_paths = heapq.heappop(solution_set)
                    logger.debug(f'CBS terminate with solution with paths {paths} and costs {cost_paths}')
                    return paths, cost_paths, generated_nodes_ecbs, expanded_nodes_astar
                else:
                    heapq.heappush(self.open_list, open_list_element)

            ##################################################################################
            # if a collisions found create two new nodes,
            # where one position is blocked for just one AMR that is colliding
            ##################################################################################

            t1, t2, agent_1, agent_2, collision_kind = collision
            agents = [agent_1, agent_2]
            t = [t1, t2]

            agents, t = self.constraints_agent_assignment_new(agents, t, node, collision_kind)

            for a, agent in enumerate(agents):
                # Create two new nodes
                new_node = copy.deepcopy(node)

                if a == 0:  # negative constraint
                    if collision_kind == 'node':
                        # Add neg. node constraints
                        if self.check_constraints_conflict_neg_constraint(new_node['pos_constraints'],
                                                                          (node['paths'][agent][t[a]], t[a], agent)):
                            continue
                        else:
                            new_node['neg_constraints'].add((node['paths'][agent][t[a]], t[a], agent))
                    else:  # Edge collision
                        if self.check_constraints_conflict_neg_constraint(new_node['pos_constraints'],
                                                                          ((node['paths'][agent][t[a]],
                                                                            node['paths'][agent][t[a]+1]),
                                                                          t[a], agent)):
                            continue
                        else:
                            new_node['neg_constraints'].add(((node['paths'][agent][t[a]], node['paths'][agent][t[a]+1]),
                                                              t[a], agent))

                    new_node, _, expanded_nodes_astar = self.replanning_paths(new_node, agent, start_node_ids, end_node_ids, graph, layout_id,
                                                                              heuristic, expanded_nodes_astar, t[a])

                    if new_node is not None:
                        constraints_key = (
                            frozenset(new_node['neg_constraints']),
                            frozenset(new_node['pos_constraints']),
                            hash(str(new_node['paths']))
                        )
                        if constraints_key not in closed_list:
                            closed_list.add(constraints_key)
                        else:
                            continue
                        generated_nodes_ecbs += 1
                        cbs_node = (new_node['costs'], generated_nodes_ecbs, new_node['paths'], new_node['neg_constraints'],
                                    new_node['pos_constraints'], new_node['cost_paths'])
                        cbs_node = copy.deepcopy(cbs_node)

                        heapq.heappush(self.open_list, cbs_node)
                        if new_node['costs'] < self.current_f_min_value:
                            self.current_f_min_value = new_node['costs']
                            self.update_focal_list()

                elif a == 1:  # positive constraint
                    if collision_kind == 'node':
                        # Add pos. node constraints
                        if self.check_constraints_conflict_pos_constraint(new_node['pos_constraints'],(node['paths'][agents[0]][t[0]], t[0], agents[0])):
                            continue
                        else:
                            new_node['pos_constraints'].add((node['paths'][agents[0]][t[0]], t[0], agents[0]))
                            new_node['neg_constraints'].add((node['paths'][agents[0]][t[0]], t[0], tuple(
                                agent_id for agent_id in range(len(new_node['paths'])) if agent_id != agents[0])))
                            new_pos_constraint = (node['paths'][agents[0]][t[0]], t[0], agents[0])

                    else:  # Add also implicit negative constraints for all other agents
                        # Add pos. edge constraints
                        if self.check_constraints_conflict_pos_constraint(new_node['pos_constraints'],
                                                                          ((node['paths'][agents[0]][t[0]],
                                                                            node['paths'][agents[0]][t[0] + 1]),
                                                                          t[0], agents[0])):
                            continue
                        else:
                            new_node['pos_constraints'].add(((node['paths'][agents[0]][t[0]], node['paths'][agents[0]][t[0] + 1]),
                                                             t[0], agents[0]))
                            new_node['neg_constraints'].add(((node['paths'][agents[0]][t[0]], node['paths'][agents[0]][t[0] + 1]),
                                                             t[0], tuple(agent_id for agent_id in range(len(new_node['paths'])) if agent_id != agents[0])))
                            new_pos_constraint = ((node['paths'][agents[0]][t[0]], node['paths'][agents[0]][t[0] + 1]),
                                                  t[0], agents[0])

                    node_changes = False
                    for a_p, agent_path in enumerate(new_node['paths']):
                        if a_p == agents[0]:
                            continue  # Agent get positive constraints
                        if self.violates_constraints(agent_path, new_pos_constraint):
                            new_node, node_changes, expanded_nodes_astar = self.replanning_paths(new_node, a_p,
                                                                                                 start_node_ids,
                                                                                                 end_node_ids,
                                                                                                 graph, layout_id,
                                                                                                 heuristic,
                                                                                                 expanded_nodes_astar,
                                                                                                 t[0])
                    if node_changes is True and new_node is not None:
                        new_node['costs'] = cbs_cost_function(new_node['cost_paths'])
                        constraints_key = (
                            frozenset(new_node['neg_constraints']),
                            frozenset(new_node['pos_constraints']),
                            hash(str(new_node['paths']))
                        )
                        if constraints_key not in closed_list:
                            closed_list.add(constraints_key)
                        else:
                            continue
                        generated_nodes_ecbs += 1
                        # new_node = self.delete_pos_constraints_after_path_planning(new_node, agents, t)
                        cbs_node = (new_node['costs'], generated_nodes_ecbs, new_node['paths'],
                                    new_node['neg_constraints'], new_node['pos_constraints'], new_node['cost_paths'])
                        cbs_node = copy.deepcopy(cbs_node)
                        heapq.heappush(self.open_list, cbs_node)
                        if new_node['costs'] < self.current_f_min_value:
                            self.current_f_min_value = new_node['costs']
                            self.update_focal_list()

            elapsed = time.monotonic()-start_time
            ############################################################################################################
            # this should not happen, but if it does the smallest element of the open list will restart the focal list
            if len(self.focal_list) == 0 and len(self.open_list) > 0:
                self.current_f_min_value = self.open_list[0][0]
                self.update_focal_list()
        ################################################################################################################
        # Open list is empty or runtime is finished
        if len(solution_set) > 0:
            costs, _id, paths, constraints, cost_paths = heapq.heappop(solution_set)
            logger.info(f'Solution set: {solution_set}')
            logger.debug(f'CBS terminate because of empty open set or no more runtime'
                         f' with a solution with paths {paths} and costs {cost_paths}')
            return paths, cost_paths, generated_nodes_ecbs, expanded_nodes_astar, constraints
        # Else, no solution found
        logger.info(f'No solvable path found with ECBS in {MAX_TIME_CBS} seconds or max number generated nodes!')
        return None, None, generated_nodes_ecbs, expanded_nodes_astar, constraints

    def check_termination(self, open_list, solution_set, node_counter):
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
        open_list_element = (costs, node_counter, paths_new_open_list_element, set(), costs_paths)
        return termination, open_list_element, node_counter

    def update_focal_list(self):
        self.focal_list = []
        bound = self.w_high * self.current_f_min_value
        # elem := (costs, paths, constraints, cost_paths)
        for elem in self.open_list:
            if elem[0] <= bound:
                heapq.heappush(self.focal_list, copy.deepcopy((self.focal_heuristic(elem[2]), elem[1], elem[0],
                                                                     elem[2], elem[3], elem[4], elem[5])))
        return

    def check_constraints_conflict_neg_constraint(self, pos_constraints_node, neg_constraint):
        conflict_nodes_neg, last_t_neg, agent_neg = neg_constraint

        agent_pos_constraints = [c for c in pos_constraints_node if c[2] == agent_neg]

        for const in agent_pos_constraints:
            conflict_nodes, last_t, agent = const
            if last_t == last_t_neg:
                if isinstance(conflict_nodes, str):
                    if isinstance(conflict_nodes_neg, str):
                        if conflict_nodes == conflict_nodes_neg:
                            return True
                    elif isinstance(conflict_nodes_neg, tuple):
                        if conflict_nodes == conflict_nodes_neg[0]:
                            return True
            elif last_t + 1 == last_t_neg:
                if isinstance(conflict_nodes, tuple):
                    if isinstance(conflict_nodes_neg, str):
                        if conflict_nodes[1] == conflict_nodes_neg:
                            return True
                    elif isinstance(conflict_nodes_neg, tuple):
                        if conflict_nodes[1] == conflict_nodes_neg[0]:
                            return True
        return False

    def check_constraints_conflict_pos_constraint(self, pos_constraints_node, pos_constraint):
        new_nodes, new_t, new_agent = pos_constraint
        agent_pos_constraints = [c for c in pos_constraints_node if c[2] == new_agent]
        for nodes, t, agent in agent_pos_constraints:
            if t == new_t and nodes != new_nodes:
                return True
            if isinstance(nodes, tuple) and isinstance(new_nodes, tuple):
                if t == new_t and (nodes[0] == new_nodes[1] and nodes[1] == new_nodes[0]):
                    return True
        return False

    def conflict_intersects_existing_pos_constraint_status(self, pos_constraint, pos_constraints_agent):
        if len(pos_constraints_agent) < 1:
            return 'vergleich'
        else:
            conflict_nodes, last_t, _ = max(pos_constraints_agent, key=lambda c: c[1])
            new_conflict_node, new_t = pos_constraint
            if new_t < last_t:
                return 'ablehnen'
            elif new_t == last_t:
                if isinstance(conflict_nodes, tuple):
                    if isinstance(new_conflict_node, tuple):
                        if conflict_nodes[0] == new_conflict_node[0] and conflict_nodes[1] == new_conflict_node[1]:
                            return 'nehmen'
                        else:
                            return 'ablehnen'
                    else:
                        if conflict_nodes[0] == new_conflict_node:
                            return 'nehmen'
                        else:
                            return 'ablehnen'
                else:
                    if isinstance(new_conflict_node, tuple):
                        if conflict_nodes == new_conflict_node[0]:
                            return 'vergleich'
                        else:
                            return 'ablehnen'
                    else:
                        if conflict_nodes == new_conflict_node:
                            return 'nehmen'
                        else:
                            return 'ablehnen'
            elif new_t == last_t + 1:
                if isinstance(conflict_nodes, tuple):
                    if not isinstance(new_conflict_node, tuple):
                        if conflict_nodes[1] == new_conflict_node:
                            return 'nehmen'
                        else:
                            return 'ablehnen'
                    else:
                        if conflict_nodes[1] == new_conflict_node[0]:
                            return 'vergleich'
                        else:
                            return 'ablehnen'
                else:
                    return 'vergleich'
            else:

                return 'vergleich'


    def replanning_paths(self, new_node, agent, start_node_ids, end_node_ids, graph, layout_id, heuristic,
                         expanded_nodes, time_new_constraint):
        agent_pos_constraints = sorted([c for c in new_node['pos_constraints'] if c[2] == agent], key=lambda x: x[1])

        prev_c = (start_node_ids[agent], 0)
        next_c = (end_node_ids[agent], np.inf)

        for c in agent_pos_constraints:
            if c[1] <= time_new_constraint:
                prev_c = c
            elif c[1] > time_new_constraint and c[1] < next_c[1]:
                next_c = c

        if isinstance(prev_c[0], tuple):
            start_node_for_segment, t_start = prev_c[0][1], prev_c[1] + 1
        else:
            start_node_for_segment, t_start = prev_c[0], prev_c[1]

        if isinstance(next_c[0], tuple):
            end_node_for_segment, t_end = next_c[0][0], next_c[1]
        else:
            end_node_for_segment, t_end = next_c[0], next_c[1]


        if start_node_for_segment != end_node_for_segment:
            focal_search = self.focal_search(graph, layout_id, start_node_for_segment, end_node_for_segment,
                                             new_node['neg_constraints'], heuristic, agent, t_start, t_end)
            other_paths = new_node['paths'][:agent] + new_node['paths'][agent + 1:]
            other_paths_shifted = [path[t_start:] for path in other_paths]
            focal_search.init_focal(self.w_low, self.focal_heuristic, other_paths_shifted)
            new_path, costs, add_expanded_nodes = focal_search.compute_path()
            expanded_nodes += add_expanded_nodes
            logger.debug(f'New computed path: {new_path} with costs {costs}')
            if new_path is not None:
                if t_start == 0:
                    if t_end == np.inf:
                        new_node['paths'][agent] = new_path
                    else:
                        new_node['paths'][agent] = new_path + new_node['paths'][agent][t_end:]
                else:
                    if t_end == np.inf:
                        new_node['paths'][agent] = new_node['paths'][agent][:t_start] + new_path
                    else:
                        new_node['paths'][agent] = (new_node['paths'][agent][:t_start] + new_path +
                                                    new_node['paths'][agent][t_end:])
                new_node['cost_paths'][agent] = get_costs_for_path(new_node['paths'][agent])
                new_node['costs'] = cbs_cost_function(new_node['cost_paths'])
                return new_node, True, expanded_nodes
        return None, False, expanded_nodes

    def violates_constraints(self, path: List[str], constraints):
        if isinstance(constraints[0], tuple):
            # edge constraint
            if constraints[1] >= len(path) - 1:
                return False
            if (path[constraints[1]] == constraints[0][0] and path[constraints[1]+1] == constraints[0][1] or
                    path[constraints[1]+1] == constraints[0][0] and path[constraints[1]] == constraints[0][1]):
                return True
        else:
            if isinstance(constraints[1], tuple):
                if constraints[1][0] < len(path):
                    for follow_node in path[constraints[1][0]:]:
                        if follow_node == constraints[0]:
                            return True
                else:
                    if path[-1] == constraints[0]:
                        return True
                    else:
                        return False
            else:
                if constraints[1] < len(path):
                    if path[constraints[1]] == constraints[0]:
                        return True
                else:
                    if path[-1] == constraints[0]:
                        return True
        return False

    def constraints_agent_assignment_new(self, agents, t, node, collision_kind):

        for a, agent in enumerate(agents):
            if collision_kind == 'node':
                conflict_loc = node['paths'][agent][t[a]]
            else:
                conflict_loc = (
                    node['paths'][agent][t[a]],
                    node['paths'][agent][t[a]+1]
                )
            pos_constraints = [c for c in node['pos_constraints'] if c[2] == agent]
            for c in pos_constraints:
                loc_c, time_c, agent_c = c
                if time_c == t[a] and loc_c == conflict_loc:
                    return [agents[1-a], agents[a]], [t[1-a], t[a]]

        if t[0] < t[1]:
            return [agents[1], agents[0]], [t[1], t[0]]
        elif t[0] == t[1]:
            len_a0 = len(node['paths'][agents[0]]) - t[0]
            len_a1 = len(node['paths'][agents[1]]) - t[1]
            if len_a0 >= len_a1:
                return [agents[0], agents[1]], [t[0], t[1]]
            else:
                return [agents[1], agents[0]], [t[1], t[0]]
        else:
            return [agents[0], agents[1]], [t[0], t[1]]


