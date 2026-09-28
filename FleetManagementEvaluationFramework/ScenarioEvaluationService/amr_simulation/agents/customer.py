import heapq
from typing import List
import logging
import copy

from data.models import NewOrderInfo
import config.config_file

logger = logging.getLogger(config.config_file.LOGGER_NAME)


class Customer:
    def __init__(self, order_queue: List):
        self._order_queue = order_queue

    def add_order_to_queue(self, request_body: NewOrderInfo):
        """
        :param request_body: NewOrderInfo
        :return: send order to determine publish time to the fleet management system
        """
        logger.info(f'Get new Order Info for Order id {request_body.orderId} with publish time {request_body.publishTime}')
        heapq.heappush(self._order_queue, (request_body.publishTime.replace(tzinfo=None), len(self._order_queue),
                                           copy.deepcopy(request_body)))
