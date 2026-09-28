from enum import Enum


class OrderStatus(str, Enum):
    NEW = "NEW"
    PLANNED = "PLANNED"
    STARTED = "STARTED"
    PICKUP = "PICKUP"
    DROPOFF = "DROPOFF"
    FINISHED = "FINISHED"


class BlockingType(str, Enum):
    NONE = 'NONE'
    SOFT = 'SOFT'
    HARD = 'HARD'


class TaskAssignmentStrategy(str, Enum):
    push_back = "push_back"
    greedy = "greedy"
    greedy_completion_time = "greedy_completion_time"
    token_passing = "token_passing"
    central = "central"


class PathPlanningHeuristic(str, Enum):
    dijkstra = 'dijkstra'
    manhattan = 'manhattan'
    euclidean = 'euclidean'


class PathPlanningStrategy(str, Enum):
    dijkstra = 'dijkstra'
    cbs = 'cbs'
    cbs_djs = 'cbs_djs'
    cbs_djs_test = 'cbs_djs_test'
    ecbs_djs = 'ecbs_djs'
    ecbs_djs_test = 'ecbs_djs_test'
    cooperative_a_star = 'cooperative_a_star'
    ecbs = 'ecbs'
    i_ecbs = 'i_ecbs'
    i_cbs = "i_cbs"
    i_cbs_geo = 'i_cbs_geo'


class PathPlanningIntegration(str, Enum):
    complete_cbs = "complete_cbs"
    two_stage = "two_stage"


class ECBSHeuristic(str, Enum):
    h4 = "h4"
    h1 = 'h1'
    h2 = 'h2'
    h3 = 'h3'
    h3_fast = 'h3_fast'
    h1_fast = 'h1_fast'
    h1_fast_costs = 'h1_fast_costs'
