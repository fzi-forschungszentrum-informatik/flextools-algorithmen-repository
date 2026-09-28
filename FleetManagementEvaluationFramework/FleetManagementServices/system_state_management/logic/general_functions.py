import datetime
from typing import List

from data.enums import BlockingType
from data.models import Node, Action, ActionParameter, NodePosition


def transform_str_to_datetime(str_datetime):
    """
    :param str_datetime: datetime object as string in different formats
    :return: datetime object in equal format for all incoming string formats
    """
    if type(str_datetime) is str:
        try:
            datetime_obj = datetime.datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S.%f')
        except:
            try:
                datetime_obj = datetime.datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S')
            except:
                try:
                    datetime_obj = datetime.datetime.strptime(str_datetime, '%Y-%m-%d %H:%M:%S')
                except:
                    try:
                        datetime_obj = datetime.datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S.%f%z')
                    except:
                        try:
                            datetime_obj = datetime.datetime.fromisoformat(str_datetime)
                        except:
                            raise Exception('Error in datetime transformation!')
    else:
        datetime_obj = str_datetime  # str_datetime is already right datetime format
    return datetime_obj


def transform_node_json_to_node_object_list(node_json) -> List[Node]:
    node_list = []
    for node in node_json:
        action_list = transform_action_json_to_action_object_list(node['actions'])
        node_list.append(Node(nodeId=node['nodeId'], sequenceId=node['sequenceId'],
                              released=node['released'],
                              nodePosition=NodePosition(x=node['nodePosition']['x'],
                                                        y=node['nodePosition']['y'],
                                                        theta=node['nodePosition']['theta'],
                                                        mapId=node['nodePosition']['mapId']),
                              actions=action_list))
    return node_list


def transform_action_json_to_action_object_list(action_json) -> List[Action]:
    action_list = []
    for action in action_json:
        action_parameter_list = []
        for act_pm in action['actionParameters']:
            action_parameter_list.append(ActionParameter(key=act_pm['key'], value=act_pm['value']))
        action_list.append(Action(actionId=action['actionId'], actionType=action['actionType'],
                                  blockingType=BlockingType(action['blockingType']),
                                  actionParameters=action_parameter_list))
    return action_list

def env_to_bool(text: str) -> bool:
    value = text.strip().lower()
    if value in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "f", "no", "n", "off"}:
        return False

    raise ValueError(f"Invalid boolean for: {text}")
