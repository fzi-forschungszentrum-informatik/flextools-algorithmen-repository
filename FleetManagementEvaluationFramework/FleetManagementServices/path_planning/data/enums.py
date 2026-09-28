from enum import Enum


class BlockingType(str, Enum):
    NONE = 'NONE'
    SOFT = 'SOFT'
    HARD = 'HARD'


class PathPlanningStrategy(str, Enum):
    dijkstra = 'dijkstra'
    cooperative_a_star = 'cooperative_a_star'
    cbs = 'cbs'
    cbs_djs = 'cbs_djs'
    ecbs = 'ecbs'
    ecbs_djs = 'ecbs_djs'
    i_ecbs = 'i_ecbs'
    i_cbs = "i_cbs"


class CollisionDetectionStrategy(str, Enum):
    classical_discrete_id = "CollisionDetection_classical_discrete_id"
    classical_intervals_id = "CollisionDetection_classical_intervals_id"
    prechecking_intervals_id = "CollisionDetection_prechecking_intervals_id"
    prechecking_intervals_geometric_full = "CollisionDetection_prechecking_intervals_geometric_full"
    prechecking_intervals_geometric_partial = "CollisionDetection_prechecking_intervals_geometric_partial"


class PathPlanningHeuristic(str, Enum):
    dijkstra = 'dijkstra'
    manhattan = 'manhattan'
    euclidean = 'euclidean'
    skewed_euclid = "skewed_euclid"


class ECBSHeuristic(str, Enum):
    h4 = "h4"
    h1 = 'h1'  # h1 fast or h1 intervals
    h2 = 'h2'
    h3 = 'h3'
    h3_fast = 'h3_fast'
    h1_fast = 'h1_fast'
    h1_fast_costs = 'h1_fast_costs'
    h1_intervals = "h1_intervals"


class CostFunction(str, Enum):
    makespan = 'makespan'
    sum_of_costs = 'sum_of_costs'

