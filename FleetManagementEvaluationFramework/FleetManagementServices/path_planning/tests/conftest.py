import pytest

from config.config_file import TEST_LIF_FILE, TEST_LIF_FILE_MAPF, TEST_LIF_FILE_WAREHOUSE
from data.enums import PathPlanningStrategy
from mapf_algorithms.collision_detection.collision_detection_classes.collision_detection_classical_discrete_id import \
    CollisionDetectionClassicalDiscreteId
from mapf_algorithms.core.path_planning_obj import PathPlanningObj
from mapf_algorithms.heuristics.path_planning_heuristics import HeuristicManhattanDistance, HeuristicDijkstra, \
    HeuristicEuclideanDistance

from mapf_algorithms.path_planning.multi_agent_path_planning.high_level.cbs import CBS
from mapf_algorithms.path_planning.multi_agent_path_planning.low_level.a_star import AStar
from mapf_algorithms.path_planning.prioritized_planning.cooperative_a_star import CooperativeAStar
from mapf_algorithms.path_planning.single_agent_path_planning.dijkstra import Dijkstra


@pytest.fixture()
def path_planning_strategies_mock(monkeypatch):
    monkeypatch.setattr(
        "config.config_file.PATH_PLANNING_STRATEGY",
        PathPlanningStrategy.dijkstra
    )
    path_planning_strategies = {'dijkstra': PathPlanningObj(TEST_LIF_FILE, Dijkstra(), HeuristicManhattanDistance())}
    return path_planning_strategies


@pytest.fixture()
def path_planning_mapf_mock():
    path_planning_strategies = {'cbs': PathPlanningObj(TEST_LIF_FILE_MAPF, CBS(AStar, CollisionDetectionClassicalDiscreteId),
                                                       HeuristicDijkstra())}
    return path_planning_strategies


@pytest.fixture()
def path_planning_mapf_mock2():
    path_planning_strategies = {'cooperative_a_star': PathPlanningObj(TEST_LIF_FILE_MAPF, CooperativeAStar(),
                                                                      HeuristicDijkstra())}
    return path_planning_strategies


@pytest.fixture()
def path_planning_strategies_mock2():
    path_planning_strategies = {
        'cooperative_a_star': PathPlanningObj(TEST_LIF_FILE, Dijkstra(), HeuristicManhattanDistance())}
    return path_planning_strategies


@pytest.fixture()
def path_planning_strategies_mock3():
    path_planning_strategies = {'cooperative_a_star': PathPlanningObj(TEST_LIF_FILE, Dijkstra(),
                                                                      HeuristicEuclideanDistance())}
    return path_planning_strategies


@pytest.fixture()
def path_planning_warehouse_mock():
    path_planning_strategies = {'cbs': PathPlanningObj(TEST_LIF_FILE_WAREHOUSE, CBS(AStar,
                                                                                    CollisionDetectionClassicalDiscreteId),
                                                       HeuristicDijkstra())}
    return path_planning_strategies
