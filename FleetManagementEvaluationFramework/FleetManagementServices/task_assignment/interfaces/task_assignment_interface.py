from abc import ABC

from api.server_api_models import NewOrderInfo


#############
# INTERFACE #
#############

class TaskAssignment(ABC):
    def dispatch(self, new_order_info: NewOrderInfo):
        pass
