import copy
import heapq
from typing import List, Type
import logging
import numpy as np
import time

from config.config_file import MAX_TIME_CBS, LOGGER_NAME
import config.config_file
from data.data_structures.extended_graph import ExtendedGraph
from interfaces.low_level_search_interface import LowLevelSearchInterface
from interfaces.path_planning_heuristic_interface import Heuristic
from interfaces.path_planning_interface import PathPlanning
from mapf_algorithms.api_services.service_processing_functions import get_costs_for_path
from mapf_algorithms.collision_detection.detectors.collision_detection import detect_collision_earliest
from mapf_algorithms.heuristics.cost_functions import cbs_cost_function


logger = logging.getLogger(LOGGER_NAME)


class CBSDisjointSplitting(PathPlanning):

    def __init__(self, low_level_search: Type[LowLevelSearchInterface]):
        self.a_star = low_level_search

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

        logger.info('Start CBS computing path with own disjoint splitting')
        number_of_agents = len(start_node_ids)
        logger.debug(f'CBS: Compute paths without collisions for {number_of_agents} Agents')
        logger.debug(f'With start locations: {start_node_ids}')
        logger.debug(f'And goal locations: {end_node_ids}')
        start_time = time.monotonic()
        elapsed = time.monotonic() - start_time
        generated_nodes_cbs = 1
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

        for i in range(number_of_agents):
            a_star = self.a_star(graph.graph, layout_id, start_node_ids[i], end_node_ids[i], root['neg_constraints'],
                                 heuristic, i)
            path, costs, add_expanded_nodes_astar = a_star.compute_path()
            expanded_nodes_astar += add_expanded_nodes_astar
            if path is None:
                # there exists no solution if no path is found without constraints
                logger.exception(f'No solvable path found with CBS, because of assumption error of MAPF')
                return None, None, generated_nodes_cbs, expanded_nodes_astar, None
            root['paths'].append(path)
            root['cost_paths'].append(get_costs_for_path(path))
        root['costs'] = cbs_cost_function(root['cost_paths'])
        open_list = []
        closed_list = set()

        heapq.heappush(open_list, copy.deepcopy((root['costs'], generated_nodes_cbs, root['paths'], root['neg_constraints'],
                                                 root['pos_constraints'], root['cost_paths'])))
        solution_set = []

        while (open_list and round(elapsed) < MAX_TIME_CBS and
               config.config_file.MAX_GENERATED_NODES_CBS >= generated_nodes_cbs):
            logger.debug(f'Open list CBS: {open_list}')
            costs, _id, paths, neg_constraints, pos_constraints, cost_paths = heapq.heappop(open_list)
            node = {
                'neg_constraints': neg_constraints,
                'pos_constraints': pos_constraints,
                'paths': paths,
                'costs': costs,
                'cost_paths': cost_paths
            }
            collision = detect_collision_earliest(node['paths'])
            if collision is None:
                if config.config_file.CBS_COST_FUNCTION_IMPROVEMENT is False:
                    logger.debug(
                        str('CBS found solution with paths ' + str(node['paths']) + ' and costs ' + str(
                            node['cost_paths'])))
                    return node['paths'], node['cost_paths'], generated_nodes_cbs, expanded_nodes_astar, node["neg_constraints"]
                else:
                    logger.debug(str('CBS found possible solution with paths ' + str(node['paths']) + ' and costs ' +
                                     str(node['cost_paths'])))
                    heapq.heappush(solution_set, (node['costs'], node['paths'], node['neg_constraints'],
                                                  node['cost_paths']))
                    logger.debug(f'Current solution set: {solution_set}')
                continue

            if len(solution_set) > 0:
                termination, open_list_element, node_counter = self.check_termination(open_list, solution_set, generated_nodes_cbs)
                if termination is True:
                    logger.info(f'Solution set: {solution_set}')
                    costs, _id, paths, neg_constraints, cost_paths = heapq.heappop(solution_set)
                    logger.debug(f'CBS terminate with solution with paths {paths} and costs {cost_paths}')
                    return paths, cost_paths, generated_nodes_cbs, expanded_nodes_astar, neg_constraints
                else:
                    heapq.heappush(open_list, open_list_element)

            t1, t2, agent_1, agent_2, collision_kind = collision
            agents = [agent_1, agent_2]
            t = [t1, t2]

            agents, t = self.constraints_agent_assignment_new(agents, t, node, collision_kind)

            for a, agent in enumerate(agents):
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
                        if self.check_constraints_conflict_neg_constraint(new_node['pos_constraints'],((node['paths'][agent][t[a]], node['paths'][agent][t[a]+1]),
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
                        generated_nodes_cbs += 1
                        cbs_node = (new_node['costs'], generated_nodes_cbs, new_node['paths'], new_node['neg_constraints'],
                                    new_node['pos_constraints'], new_node['cost_paths'])
                        cbs_node = copy.deepcopy(cbs_node)
                        heapq.heappush(open_list, cbs_node)

                elif a == 1:  # positive constraint
                    if collision_kind == 'node':
                        # Add pos. node constraints
                        if self.check_constraints_conflict_pos_constraint(new_node['pos_constraints'],(node['paths'][agents[0]][t[0]], t[0], agents[0])):
                            continue
                        else:
                            new_node['pos_constraints'].add((node['paths'][agents[0]][t[0]], t[0], agents[0]))
                            new_node['neg_constraints'].add((node['paths'][agents[0]][t[0]], t[0], tuple(
                                agent_id for agent_id in range(len(new_node['paths'])) if
                                agent_id != agents[0])))
                            new_pos_constraint = (node['paths'][agents[0]][t[0]], t[0], agents[0])
                    else:  # Add also implicit negative constraints for all other agents
                        # Add pos. edge constraints
                        if self.check_constraints_conflict_pos_constraint(new_node['pos_constraints'], ((node['paths'][agents[0]][t[0]], node['paths'][agents[0]][t[0] + 1]),
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
                                                                                                 start_node_ids, end_node_ids,
                                                                           graph, layout_id, heuristic, expanded_nodes_astar, t[0])
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
                        generated_nodes_cbs += 1
                        cbs_node = (new_node['costs'], generated_nodes_cbs, new_node['paths'], new_node['neg_constraints'],
                                    new_node['pos_constraints'], new_node['cost_paths'])
                        cbs_node = copy.deepcopy(cbs_node)
                        heapq.heappush(open_list, cbs_node)
            elapsed = time.monotonic()-start_time

        # Open list is empty or runtime is finished
        if len(solution_set) > 0:
            costs, _id, paths, neg_constraints, cost_paths = heapq.heappop(solution_set)
            logger.info(f'Solution set: {solution_set}')
            logger.debug(f'CBS terminate because of empty open set or no more runtime'
                         f' with a solution with paths {paths} and costs {cost_paths}')
            return paths, cost_paths, generated_nodes_cbs, expanded_nodes_astar, neg_constraints
        # Else, no solution found
        logger.info(f'No solvable path found with CBS in {MAX_TIME_CBS} seconds or max number generated nodes!')
        return None, None, generated_nodes_cbs, expanded_nodes_astar, None

    def check_termination(self, open_list, solution_set, node_counter):
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
            # node constraint
                if constraints[1] < len(path):
                    if path[constraints[1]] == constraints[0]:
                        return True
                else:
                    if path[-1] == constraints[0]:
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

    def replanning_paths(self, new_node, agent, start_node_ids, end_node_ids, graph, layout_id, heuristic,
                         expanded_nodes_astar, time_new_constraint):
        if new_node['pos_constraints'] is not None:
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
        else:
            start_node_for_segment, t_start = start_node_ids[agent], 0
            end_node_for_segment, t_end = end_node_ids[agent], np.inf

        if start_node_for_segment != end_node_for_segment:
            a_star = self.a_star(graph.graph, layout_id, start_node_for_segment, end_node_for_segment,
                                 new_node['neg_constraints'], heuristic, agent, t_start, t_end)
            new_path, costs, add_expanded_nodes_astar = a_star.compute_path()
            expanded_nodes_astar += add_expanded_nodes_astar
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
                return new_node, True, expanded_nodes_astar
        return new_node, False, expanded_nodes_astar

    def delete_pos_constraints_after_path_planning(self, new_node, agents, times):
        collision_new = detect_collision_earliest([new_node['paths'][agents[0]], new_node['paths'][agents[1]]])
        if collision_new is not None:
            t1_new, t2_new, agent_1_new, agent_2_new, _ = collision_new
            if t1_new < times[0] or t2_new < times[1]:
                agents_involved = [agent_1_new, agent_2_new]
                time_new = [t1_new, t2_new]
                for ac, agent_check in enumerate(agents_involved):
                    agent_pos_constraints = [c for c in new_node['pos_constraints'] if c[2] == agent_check]
                    for c in list(agent_pos_constraints):
                        locations, t_constraint, _ = c
                        if t_constraint >= time_new[ac]:
                            new_node['pos_constraints'].remove(c)
                            continue
        return new_node

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






