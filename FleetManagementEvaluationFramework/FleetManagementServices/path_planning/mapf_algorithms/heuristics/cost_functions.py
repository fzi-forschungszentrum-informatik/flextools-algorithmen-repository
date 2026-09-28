import numpy as np

import config
from data.enums import CostFunction


def cbs_cost_function(paths):
    costs = None
    if config.config_file.COST_FUNCTION == CostFunction.makespan:
        costs = np.max(paths)
    elif config.config_file.COST_FUNCTION == CostFunction.sum_of_costs:
        costs = np.sum(paths)
    return costs
