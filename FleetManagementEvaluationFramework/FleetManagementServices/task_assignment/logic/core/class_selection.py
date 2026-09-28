from data.enums import TaskAssignmentStrategy
from data.models import ActionIdCounter
import config.config_file
from logic.task_assignment.central import Central
from logic.task_assignment.greedy import Greedy
from logic.task_assignment.greedy_earliest_completion import GreedyCompletionTime
from logic.task_assignment.pushback import PushBack
from logic.task_assignment.token_passing import TokenPassing


def get_dispatching_interface(action_id_counter: ActionIdCounter):
    interface = None
    if config.config_file.TASK_ASSIGNMENT_STRATEGY == TaskAssignmentStrategy.greedy:
        interface = Greedy(action_id_counter)
    elif config.config_file.TASK_ASSIGNMENT_STRATEGY == TaskAssignmentStrategy.push_back:
        interface = PushBack(action_id_counter)
    elif config.config_file.TASK_ASSIGNMENT_STRATEGY == TaskAssignmentStrategy.greedy_completion_time:
        interface = GreedyCompletionTime(action_id_counter)
    elif config.config_file.TASK_ASSIGNMENT_STRATEGY == TaskAssignmentStrategy.token_passing:
        interface = TokenPassing(action_id_counter)
    elif config.config_file.TASK_ASSIGNMENT_STRATEGY == TaskAssignmentStrategy.central:
        interface = Central(action_id_counter)
    return interface
