import math
import random

from config.config_file import FOCAL_RANDOM_SEED, H4_MULT

from mapf_algorithms.api_services.service_processing_functions import get_costs_for_path
from mapf_algorithms.heuristics.cost_functions import cbs_cost_function

from collections import defaultdict
from typing import List, Tuple, Union


def h2(paths):
    """
    :param paths: List of planned paths for amr`s
    :return: number of amr that have collisions
    """
    amr_coll = 0
    i = 0
    while i < len(paths):
        agent_path = paths[i]
        j = i + 1
        collision_found = False
        while j < len(paths):
            agent_path_2 = paths[j]
            if agent_path and agent_path_2:
                for t in range(max(len(agent_path), len(agent_path_2))):
                    t1 = min(t, len(agent_path) - 1)
                    t2 = min(t, len(agent_path_2) - 1)
                    if agent_path[t1] == agent_path_2[t2]:
                        # Vertex collision detected
                        amr_coll += 1
                        collision_found = True
                        break
                    if t1 + 1 < len(agent_path) and t2 + 1 < len(agent_path_2):
                        if (agent_path[t1] == agent_path_2[t2 + 1] and
                                agent_path[t1 + 1] == agent_path_2[t2]):
                            # Edge collision detected
                            if (agent_path[t1 + 1] == agent_path_2[t2] and
                                    agent_path[t1] == agent_path_2[t2 + 1]):
                                amr_coll += 1
                                collision_found = True
                                break
            if collision_found:
                break
            j += 1
        i += 1
    return amr_coll


def h3(paths):
    """
    :param paths: List of planned paths for amr`s
    :return: number of pairwise collisions in the CT-Node
    """
    pw_coll = 0
    for i, agent_path in enumerate(paths):
        for j, agent_path_2 in enumerate(paths[(i+1):], start=i+1):
            for t in range(max(len(agent_path), len(agent_path_2))):
                if len(agent_path) < 0 or len(agent_path_2) <= 0:
                    break
                t1 = min(t, len(agent_path)-1)
                t2 = min(t, len(agent_path_2)-1)

                if agent_path[t1] == agent_path_2[t2]:
                    # Vertex collision detected
                    pw_coll += 1
                    break
                if t1 + 1 < len(agent_path) and t2 + 1 < len(agent_path_2):
                    # Edge collision detected
                    if (agent_path[t1 + 1] == agent_path_2[t2] and
                            agent_path[t1] == agent_path_2[t2 + 1]):
                        pw_coll += 1
                        break
    return pw_coll


def h1_fast(paths):
    """
    Optimized heuristic:
    - terminates early, if all actions finished
    - consider vertex- and edge collisions more efficient
    """
    pw_coll = 0
    positions = [p[0] if p else None for p in paths]
    steps_done = [0] * len(paths)
    max_len = max(len(p) for p in paths)

    for t in range(max_len):
        pos_map = defaultdict(list)
        edge_map = {}

        # count agent
        for i, path in enumerate(paths):
            if not path:
                continue
            if steps_done[i] < len(path) - 1:
                old_pos = positions[i]
                new_pos = path[steps_done[i] + 1]
                edge = (old_pos, new_pos)
                if edge[::-1] in edge_map:
                    pw_coll += 1
                else:
                    edge_map[edge] = i
                positions[i] = new_pos
                steps_done[i] += 1
            pos_map[positions[i]].append(i)

        # check vertex collisions
        for agents in pos_map.values():
            if len(agents) > 1:
                pw_coll += len(agents) - 1

        # terminate condition
        if all(steps_done[i] >= len(paths[i]) - 1 for i in range(len(paths))):
            break

    return pw_coll

def h3_fast(paths):
    """
    Faster heuristic
    Counts how many agent pairs have at least on collision.
    """
    max_t = max(len(p) for p in paths)

    collided_pairs = set()  # save agent collision pairs (i, j) that already collided

    # vertex collisions
    for t in range(max_t):
        pos_map = defaultdict(list)
        for agent_id, path in enumerate(paths):
            pos = path[min(t, len(path) - 1)]
            pos_map[pos].append(agent_id)

        for agents in pos_map.values():
            if len(agents) > 1:
                for i in range(len(agents)):
                    for j in range(i + 1, len(agents)):
                        collided_pairs.add((agents[i], agents[j]))

    # edge collisions
    for t in range(max_t - 1):
        edge_map = {}
        for agent_id, path in enumerate(paths):
            if t + 1 < len(path):
                edge = (path[t], path[t + 1])
                if edge[::-1] in edge_map:
                    other_agent = edge_map[edge[::-1]]
                    pair = tuple(sorted((agent_id, other_agent)))
                    collided_pairs.add(pair)
                else:
                    edge_map[edge] = agent_id

    return len(collided_pairs)


def h1_fast_costs(paths):
    """
    Add path costs to heuristic solution
    """
    pw_coll = 0
    timestep_dict = defaultdict(list)

    max_t = max(len(p) for p in paths)
    for agent_id, path in enumerate(paths):
        if not path:
            continue
        for t in range(max_t):
            pos = path[min(t, len(path) - 1)]
            timestep_dict[t].append((agent_id, pos))

    for t, agent_positions in timestep_dict.items():
        pos_map = defaultdict(list)
        for agent_id, pos in agent_positions:
            pos_map[pos].append(agent_id)
        for agents in pos_map.values():
            if len(agents) > 1:
                # Vertex collision
                pw_coll += len(agents) - 1

    for t in range(max_t - 1):
        edge_map = {}
        for agent_id, path in enumerate(paths):
            if t + 1 < len(path):
                edge = (path[t], path[t + 1])
                if edge[::-1] in edge_map:
                    pw_coll += 1
                else:
                    edge_map[edge] = agent_id
    costs_list = [get_costs_for_path(path) for path in paths]
    if costs_list is not None:
        return pw_coll + cbs_cost_function(costs_list)
    else:
        return pw_coll


def h4(paths):
    """
    :param paths: Paths
    :return:  h1-fast value, but don't consider each path
    """
    random.seed(FOCAL_RANDOM_SEED)
    # Calculate log(n), rounded down to nearest integer (at least 1)
    k = max(1, int( math.sqrt(len(paths)) * H4_MULT))
    # Sample k random elements
    selected_items = random.sample(paths[:-1], k)
    return h1_fast(selected_items + paths[-1])


def h1_intervals(paths: List[List[Tuple[str, Tuple[float, float]]]]) -> int:
    """
    Counts conflicts with overlapping intervals
    """
    pw_coll = 0
    vertex_dict = defaultdict(list)
    edge_dict = defaultdict(list)

    for agent_id, path in enumerate(paths):
        for i, (node, (start, end)) in enumerate(path):
            vertex_dict[node].append((agent_id, start, end))
            if i < len(path) - 1:
                next_node, (next_start, next_end) = path[i + 1]
                edge = (node, next_node)
                edge_dict[edge].append((agent_id, start, end))  # Moving from start to end

    # Check vertex collisions
    for node, intervals in vertex_dict.items():
        intervals.sort(key=lambda x: x[1])  # sort according to start time
        for i in range(len(intervals)):
            a_id, a_start, a_end = intervals[i]
            for j in range(i + 1, len(intervals)):
                b_id, b_start, b_end = intervals[j]
                if a_end > b_start:  # overlapping intervals
                    pw_coll += 1
                else:
                    break  # because sorted, no further conflict possible

    # Check edge collisions
    for (u, v), intervals_uv in edge_dict.items():
        if (v, u) not in edge_dict:
            continue
        intervals_vu = edge_dict[(v, u)]
        for a_id, a_start, a_end in intervals_uv:
            for b_id, b_start, b_end in intervals_vu:
                if a_start < b_end and b_start < a_end:
                    pw_coll += 1

    return pw_coll


def h1(paths: Union[List[List[str]], List[List[Tuple[str, Tuple[float, float]]]]]) -> int:
    if not paths or not paths[0]:
        return 0

    first_entry = paths[0][0]

    if isinstance(first_entry, str):
        return h1_fast(paths)
    elif isinstance(first_entry, tuple) and isinstance(first_entry[1], tuple):
        return h1_intervals(paths)
    else:
        raise ValueError("Unknown format!")








