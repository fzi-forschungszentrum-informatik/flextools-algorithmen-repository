import copy
from typing import List

from data.models import NodeState
import data.db_init


def transform_node_states_to_tokens(node_states: List[NodeState], last_node_id: str):
    token_list = []
    if len(node_states) > 0:
        for node in node_states:
            token_list.append(node.nodeId)
            if node.nodeDescription == 'Action':
                token_list.append('Event')
    else:
        token_list.append(last_node_id)
    return token_list


def get_system_states_for_all_amrs():
    system_state_list = []  # Get system state for all amr's
    for key in data.db_init.database['system_state_management'].amr_states.keys():
        system_state_list.append(copy.deepcopy(data.db_init.database['system_state_management'].amr_states[key]))
    for sys_state in system_state_list:
        while 'Event' in sys_state.token:
            sys_state.token.remove('Event')
    return system_state_list
