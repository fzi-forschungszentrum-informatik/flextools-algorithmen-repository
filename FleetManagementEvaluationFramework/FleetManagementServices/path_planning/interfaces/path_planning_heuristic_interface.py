from abc import ABC
import logging

from config.config_file import LOGGER_NAME
from data.models import Node

logger = logging.getLogger(LOGGER_NAME)


class Heuristic(ABC):
    def __init__(self):
        self.layouts = {}

    def set_layout(self, layout_id, layout):
        self.layouts[layout_id] = layout

    def heuristic_costs_to_goal(self, *args, **kwargs):
        pass

    def get_node_infos_node_id(self, node_id: str, layout_id: str) -> Node:
        """
        :param node_id: node identification
        :param layout_id: layout identification
        :return:  get the node object from the layout information file
        """
        node_object = None
        if layout_id not in self.layouts.keys():
            logger.exception('Error: Layout not initialized in path planning heuristic!')
            raise Exception('Error: Layout not initialized in path planning heuristic!')
        for node in self.layouts[layout_id].nodes:
            if node.nodeId == node_id:
                node_object = node
                break
        if node_object is None:
            logger.exception(f'No node information found for node {node_id}')
            raise Exception(f'No node information found for node {node_id}')
        return node_object
