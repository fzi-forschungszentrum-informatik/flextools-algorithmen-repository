import logging
from collections import defaultdict

from config.config_file import LOGGER_NAME



logger = logging.getLogger(LOGGER_NAME)


def detect_collision_classical(paths):
    """
    :param paths: List of planned paths for amr`s
    :return: collision time, agents, and collision kind, e.g. edge or node
    """
    for i, agent_path in enumerate(paths):
        for j, agent_path_2 in enumerate(paths[(i+1):], start=i+1):
            for t in range(max(len(agent_path), len(agent_path_2))):
                t1 = min(t, len(agent_path)-1)
                t2 = min(t, len(agent_path_2)-1)
                if agent_path[t1] == agent_path_2[t2]:
                    # Vertex collision detected
                    collision_kind = 'node'
                    return t1, t2, i, j, collision_kind
                if t1 + 1 < len(agent_path) and t2 + 1 < len(agent_path_2):
                    # Edge collision detected
                    if (agent_path[t1+1] == agent_path_2[t2] and
                            agent_path[t1] == agent_path_2[t2+1]):
                        collision_kind = 'edge'
                        return t1, t2, i, j, collision_kind
    return None


def detect_collision_earliest(paths):
    """
    :param paths: List of planned paths for amr`s
    :return: collision time, agents, and collision kind, e.g. edge or node, the earliest collision at first
    """
    node_occ = defaultdict(list)  # (node, t) -> [agent_ids]
    edge_occ = defaultdict(list)  # ((u, v), t) -> [agent_ids]
    earliest_conflict = None
    earliest_t = float('inf')
    max_len = max(len(p) for p in paths)

    for agent_id, path in enumerate(paths):
        last_loc = path[-1]
        for t in range(max_len):
            loc = path[t] if t < len(path) else last_loc
            node_occ[(loc, t)].append((agent_id, min(t, len(path)-1)))
            if t < len(path) - 1:
                edge_occ[((path[t], path[t + 1]), t)].append((agent_id, t))

    for (loc, t), entries in node_occ.items():
        if len(entries) > 1 and t < earliest_t:
            a1, t1 = entries[0]
            a2, t2 = entries[1]
            earliest_conflict = (t1, t2, a1, a2, 'node')
            earliest_t = t

    for ((u, v), t), entries in edge_occ.items():
        if ((v, u), t) in edge_occ:
            for a1, t1 in entries:
                for a2, t2 in edge_occ[(v, u), t]:
                    if a1 != a2 and t < earliest_t:
                        earliest_conflict = (t1, t2, a1, a2, 'edge')
                        earliest_t = t
    return earliest_conflict