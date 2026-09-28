import config.config_file
from data.enums import PathPlanningStrategy, PathPlanningHeuristic, ECBSHeuristic, CollisionDetectionStrategy

from mapf_algorithms.collision_detection.collision_detection_classes.collision_detection_classical_discrete_id import \
    CollisionDetectionClassicalDiscreteId
from mapf_algorithms.collision_detection.collision_detection_classes.collision_detection_classical_intervals_id import \
    CollisionDetectionClassicalIntervalsId
from mapf_algorithms.collision_detection.collision_detection_classes.collision_detection_prechecking_intervals_geometric_full import \
    CollisionDetectionPrecheckingIntervalsGeometricFull
from mapf_algorithms.collision_detection.collision_detection_classes.collision_detection_prechecking_intervals_geometric_partial import \
    CollisionDetectionPrecheckingIntervalsGeometricPartial
from mapf_algorithms.collision_detection.collision_detection_classes.collision_detection_prechecking_intervals_id import \
    CollisionDetectionPrecheckingIntervalsId
from mapf_algorithms.path_planning.multi_agent_path_planning.high_level.cbs import CBS

from mapf_algorithms.path_planning.multi_agent_path_planning.high_level.cbs_disjoint_splitting import \
    CBSDisjointSplitting

from mapf_algorithms.path_planning.multi_agent_path_planning.high_level.ecbs import ECBS
from mapf_algorithms.path_planning.multi_agent_path_planning.high_level.ecbs_with_disjoint_splitting import \
    ECBSDisjointSplitting

from mapf_algorithms.path_planning.multi_agent_path_planning.low_level.a_star import AStar
from mapf_algorithms.path_planning.multi_agent_path_planning.low_level.a_star_with_agent_specific_constraints import \
    AStarDisjointSplitting
from mapf_algorithms.path_planning.multi_agent_path_planning.low_level.focal_search import FocalSearch
from mapf_algorithms.path_planning.multi_agent_path_planning.low_level.focal_search_with_agent_specific_constraints import \
    FocalSearchDisjointSplitting
from mapf_algorithms.path_planning.multi_agent_path_planning.low_level.interval_astar import IntervalAStar
from mapf_algorithms.path_planning.multi_agent_path_planning.low_level.interval_focal_search import IntervalFocalSearch

from mapf_algorithms.path_planning.prioritized_planning.cooperative_a_star import CooperativeAStar
from mapf_algorithms.path_planning.single_agent_path_planning.dijkstra import Dijkstra
from mapf_algorithms.heuristics.focal_heuristics import h1, h2, h3, h4, h3_fast, h1_fast, h1_fast_costs, \
     h1_intervals
from mapf_algorithms.heuristics.path_planning_heuristics import HeuristicManhattanDistance, HeuristicEuclideanDistance, \
    HeuristicDijkstra, HeuristicSkewedEuclideanDistance


def get_path_planning_interface():
    interface = None
    if config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.dijkstra:
        interface = Dijkstra()
    elif config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.cooperative_a_star:
        interface = CooperativeAStar()
    ###############################################################################################
    elif config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.cbs:
        interface = CBS(get_low_level_search(), get_collision_detection_class())
    elif config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.ecbs:
        interface = ECBS(config.config_file.OPTIMALITY_BOUND, get_ecbs_heuristic_interface(),
                         get_low_level_search(), get_collision_detection_class())
    ###############################################################################################
    elif config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_cbs:
        interface = CBS(get_low_level_search(), get_collision_detection_class())
    elif config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_ecbs:
        interface = ECBS(config.config_file.OPTIMALITY_BOUND, get_ecbs_heuristic_interface(),
                          get_low_level_search(), get_collision_detection_class())
    ######################## DISJOINT-SPLITTING ######################################################
    elif config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.cbs_djs:
        interface = CBSDisjointSplitting(get_low_level_search())
    elif config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.ecbs_djs:
        interface = ECBSDisjointSplitting(get_low_level_search(), config.config_file.OPTIMALITY_BOUND,
                                          get_ecbs_heuristic_interface())
    return interface


def get_heuristic_interface():
    interface = None
    if config.config_file.PATH_PLANNING_HEURISTIC == PathPlanningHeuristic.manhattan:
        interface = HeuristicManhattanDistance()
    elif config.config_file.PATH_PLANNING_HEURISTIC == PathPlanningHeuristic.euclidean:
        interface = HeuristicEuclideanDistance()
    elif config.config_file.PATH_PLANNING_HEURISTIC == PathPlanningHeuristic.dijkstra:
        interface = HeuristicDijkstra()
    elif config.config_file.PATH_PLANNING_HEURISTIC == PathPlanningHeuristic.skewed_euclid:
        interface = HeuristicSkewedEuclideanDistance()
    return interface


def get_collision_detection_class():
    retclass = None
    if config.config_file.COLLISION_DETECTION_STRATEGY == CollisionDetectionStrategy.classical_discrete_id:
        retclass = CollisionDetectionClassicalDiscreteId
        assert (config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.cbs or
                config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.ecbs)
    elif config.config_file.COLLISION_DETECTION_STRATEGY == CollisionDetectionStrategy.classical_intervals_id:
        retclass = CollisionDetectionClassicalIntervalsId
        assert (config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_ecbs or
                config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_cbs)
    elif config.config_file.COLLISION_DETECTION_STRATEGY == CollisionDetectionStrategy.prechecking_intervals_id:
        retclass = CollisionDetectionPrecheckingIntervalsId
        assert (config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_ecbs or
                config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_cbs)
    elif config.config_file.COLLISION_DETECTION_STRATEGY == CollisionDetectionStrategy.prechecking_intervals_geometric_full:
        retclass = CollisionDetectionPrecheckingIntervalsGeometricFull
        assert (config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_ecbs or
                config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_cbs)
    elif config.config_file.COLLISION_DETECTION_STRATEGY == CollisionDetectionStrategy.prechecking_intervals_geometric_partial:
        retclass = CollisionDetectionPrecheckingIntervalsGeometricPartial
        assert (config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_ecbs or
                config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_cbs)
    return retclass


def get_ecbs_heuristic_interface():
    interface = None
    if config.config_file.ECBS_HEURISTIC == ECBSHeuristic.h1:
        interface = h1
    elif config.config_file.ECBS_HEURISTIC == ECBSHeuristic.h1_fast:
        interface = h1_fast
    elif config.config_file.ECBS_HEURISTIC == ECBSHeuristic.h1_fast_costs:
        interface = h1_fast_costs
    elif config.config_file.ECBS_HEURISTIC == ECBSHeuristic.h2:
        interface = h2
    elif config.config_file.ECBS_HEURISTIC == ECBSHeuristic.h3:
        interface = h3
    elif config.config_file.ECBS_HEURISTIC == ECBSHeuristic.h3_fast:
        interface = h3_fast
    elif config.config_file.ECBS_HEURISTIC == ECBSHeuristic.h4:
        interface = h4
    elif config.config_file.ECBS_HEURISTIC == ECBSHeuristic.h1_intervals:
        interface = h1_intervals
    return interface


def get_low_level_search():
    interface = None
    if config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.cbs:
        interface = AStar
    elif config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.ecbs:
        interface = FocalSearch
    elif config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_cbs:
        interface = IntervalAStar
    elif config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_ecbs:
        interface = IntervalFocalSearch
    elif config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.cbs_djs:
        interface = AStarDisjointSplitting
    elif config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.ecbs_djs:
        interface = FocalSearchDisjointSplitting
    return interface



