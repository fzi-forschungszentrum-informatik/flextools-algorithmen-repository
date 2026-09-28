import json
import math

import networkx as nx
import numpy as np

from api.server_api_models import LIFObject
from config.config_file import AMR_RADIUS
from mapf_algorithms.collision_detection.collision_detection_classes.collision_detection_prechecking_intervals_geometric_partial import \
    CollisionDetectionPrecheckingIntervalsGeometricPartial

from mapf_algorithms.core.path_planning_obj import PathPlanningObj
from mapf_algorithms.heuristics.path_planning_heuristics import HeuristicSkewedEuclideanDistance

from mapf_algorithms.path_planning.multi_agent_path_planning.high_level.cbs import CBS
from mapf_algorithms.path_planning.multi_agent_path_planning.low_level.interval_astar import IntervalAStar
from tests.random_lif_generator.lif_generation_config import TEST_PP_LAYOUT_ID
from tests.random_lif_generator.lif_show import extract_time_steps, build_graph, load_lif_file


def start_path_planning(path_pairs, lif_path):

    # Load node pairs from selected file
    with open(path_pairs, "r") as f:
        pair_data = json.load(f)
        starts = pair_data["start_nodes"]
        ends = pair_data["end_nodes"]
        try:
            constraints = pair_data["constraints"]
        except:
            constraints = set()   # Consider Empty constraint class for selected algorithm


    ####################################################################################################################
    # get interfaces, from config file
    ####################################################################################################################
    path_planning_interface = CBS(IntervalAStar, CollisionDetectionPrecheckingIntervalsGeometricPartial)
    heuristic_interface = HeuristicSkewedEuclideanDistance()
    # initialise traveltime
    tt_obj = PathPlanningObj(
        '',
        path_planning_interface,
        heuristic_interface
    )
    ####################################################################################################################
    # load the LIF-object
    ####################################################################################################################
    with open(lif_path, "r") as f:
        lif_data = json.load(f)

    lif_obj = LIFObject(**lif_data)
    tt_obj.set_layout(lif_obj)

    constraints_set = {
        (node, tuple(value) if isinstance(value, list) else value)
        for node, value in constraints
    }

    paths, costs, path_constraints = tt_obj.compute_path(
        layout_id=TEST_PP_LAYOUT_ID,
        start_node_ids=starts,
        end_node_ids=ends,
        constraints=None,
        tokens=None
    )

    assert paths is not None

    return paths

def compute_amr_distances(G, paths, min_distance):
    pos = nx.get_node_attributes(G, "pos") or nx.spring_layout(G, seed=42)

    raw_times = extract_time_steps(paths)
    min_t, max_t = raw_times[0], raw_times[-1]
    duration = max_t - min_t
    NUM_STEPS = int(duration * 30)
    time_steps = np.linspace(min_t, max_t, NUM_STEPS)

    # === Interval-Preprocessing ===
    intervals = []
    for path in paths:
        p_intervals = []
        for j in range(len(path)):
            node, (t0, t1) = path[j]
            p_intervals.append((t0, t1 - 0.001, ("node", node)))

            if j < len(path) - 1:
                next_node, (nt0, nt1) = path[j + 1]
                p_intervals.append((t1 - 0.001, nt0, ("edge", node, next_node)))

        intervals.append(p_intervals)

    # === Save results === #
    violations = []

    for t in time_steps:
        positions = []
        for i, path_intervals in enumerate(intervals):
            x, y = None, None

            for t0, t1, obj in path_intervals:
                if t0 <= t <= t1:
                    if obj[0] == "node":
                        node = obj[1]
                        x, y = pos[node]

                    elif obj[0] == "edge":
                        u, v = obj[1], obj[2]
                        x0, y0 = pos[u]
                        x1, y1 = pos[v]

                        alpha = (t - t0) / (t1 - t0)
                        x = x0 + alpha * (x1 - x0)
                        y = y0 + alpha * (y1 - y0)

                    break

            if x is not None and y is not None:
                positions.append((i, x, y))

        # === Check distance between AMRs === #
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                id1, x1, y1 = positions[i]
                id2, x2, y2 = positions[j]

                dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

                if dist <= min_distance:
                    violations.append({
                        "time": t,
                        "amr1": id1,
                        "amr2": id2,
                        "distance": dist
                    })

    return violations

def test_collision_detection_small_far():
    path_pairs_file = "./tests/random_lif_generator/data/colldet_tests/small_test.json"
    lif_path = "./tests/random_lif_generator/data/colldet_tests/small_test_far.json"
    paths = start_path_planning(path_pairs_file, lif_path)

    G = build_graph(load_lif_file(lif_path))

    violations = compute_amr_distances(G, paths, 2*AMR_RADIUS + 0.001)
    assert not violations

def test_collision_detection_small_close():
    path_pairs_file = "./tests/random_lif_generator/data/colldet_tests/small_test.json"
    lif_path = "./tests/random_lif_generator/data/colldet_tests/small_test_close.json"
    paths = start_path_planning(path_pairs_file, lif_path)

    G = build_graph(load_lif_file(lif_path))

    violations = compute_amr_distances(G, paths, 2*AMR_RADIUS + 0.001)
    assert not violations

def test_collision_detection_small_close_diag():
    path_pairs_file = "./tests/random_lif_generator/data/colldet_tests/small_test.json"
    lif_path = "./tests/random_lif_generator/data/colldet_tests/small_test_close_diag.json"
    paths = start_path_planning(path_pairs_file, lif_path)

    G = build_graph(load_lif_file(lif_path))

    violations = compute_amr_distances(G, paths, 2*AMR_RADIUS + 0.001)
    assert not violations

def test_collision_detection_small_close_upper():
    path_pairs_file = "./tests/random_lif_generator/data/colldet_tests/small_test_upper.json"
    lif_path = "./tests/random_lif_generator/data/colldet_tests/small_test_close_upper.json"
    paths = start_path_planning(path_pairs_file, lif_path)

    G = build_graph(load_lif_file(lif_path))

    violations = compute_amr_distances(G, paths, 2*AMR_RADIUS + 0.001)
    assert not violations

