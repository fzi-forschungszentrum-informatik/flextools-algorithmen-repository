import logging

import data.enums
from api.server_api_models import NewOrderInfo, DispatchingStrategy, RequestOrderAMR, DeleteOrderRequest, \
    ReleaseOrderRequest, ReservedNodeRequest
import config.config_file
import logic.core.task_assignment_init
from data.models import ActionIdCounter
from logic.core.class_selection import get_dispatching_interface

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def service_dispatch_new_order(request_body: NewOrderInfo):
    #########################
    # DISPATCHING NEW ORDER #
    #########################
    dispatcher = logic.core.task_assignment_init.task_assignment_strategies[config.config_file.TASK_ASSIGNMENT_STRATEGY]
    return dispatcher.dispatch(request_body)


def service_set_dispatching_strategy(request_body: DispatchingStrategy):
    config.config_file.TASK_ASSIGNMENT_STRATEGY = data.enums.TaskAssignmentStrategy(request_body.dispatchingStrategy)
    if config.config_file.TASK_ASSIGNMENT_STRATEGY not in logic.core.task_assignment_init.task_assignment_strategies.keys():
        action_id_counter = logic.core.task_assignment_init.task_assignment_strategies[
            next(iter(logic.core.task_assignment_init.task_assignment_strategies.keys()))].action_id_counter
        dispatching_interface = get_dispatching_interface(action_id_counter)
        logic.core.task_assignment_init.task_assignment_strategies[config.config_file.TASK_ASSIGNMENT_STRATEGY] = dispatching_interface
    if request_body.useImprovement is not None:
        config.config_file.USE_IMPROVEMENT = request_body.useImprovement
        logic.core.task_assignment_init.task_assignment_strategies[config.config_file.TASK_ASSIGNMENT_STRATEGY].set_use_improvement(
            config.config_file.USE_IMPROVEMENT)
    return


def service_get_order_from_order_pool(request_body: RequestOrderAMR):
    if config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.token_passing:
        dispatcher = logic.core.task_assignment_init.task_assignment_strategies[config.config_file.TASK_ASSIGNMENT_STRATEGY]
        return dispatcher.request_order_from_amr(request_body.amrId, request_body.systemStatesAmr)
    elif config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.central:
        dispatcher = logic.core.task_assignment_init.task_assignment_strategies[config.config_file.TASK_ASSIGNMENT_STRATEGY]
        return dispatcher.process_central_after_timestep(request_body.systemStatesAmr)
    else:
        logger.exception('Error: Order pool only available with token-passing dispatching strategy!')
        raise Exception('Error: Order pool only available with token-passing dispatching strategy!')


def service_delete_order_from_order_pool(request_body: DeleteOrderRequest):
    if config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.token_passing:
        dispatcher = logic.core.task_assignment_init.task_assignment_strategies[config.config_file.TASK_ASSIGNMENT_STRATEGY]
        return dispatcher.remove_order_from_order_pool(request_body.orderId)
    elif config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.central:
        dispatcher = logic.core.task_assignment_init.task_assignment_strategies[config.config_file.TASK_ASSIGNMENT_STRATEGY]
        return dispatcher.remove_finish_executed_task(request_body.orderId)
    else:
        logger.exception('Error: Order pool only available with token-passing dispatching strategy!')
        raise Exception('Error: Order pool only available with token-passing dispatching strategy!')


def service_reset_dispatching():
    action_id_counter = ActionIdCounter(nextActionId=1)
    dispatching_interface = get_dispatching_interface(action_id_counter)
    logic.core.task_assignment_init.task_assignment_strategies[config.config_file.TASK_ASSIGNMENT_STRATEGY] = dispatching_interface
    return


def service_release_order_in_order_pool(request_body: ReleaseOrderRequest):
    if config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.token_passing:
        dispatcher = logic.core.task_assignment_init.task_assignment_strategies[config.config_file.TASK_ASSIGNMENT_STRATEGY]
        return dispatcher.release_order_again(request_body.orderId)
    elif config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.central:
        dispatcher = logic.core.task_assignment_init.task_assignment_strategies[config.config_file.TASK_ASSIGNMENT_STRATEGY]
        return dispatcher.release_order_again(request_body.orderId)
    else:
        logger.exception('Error: Order pool only available with token-passing dispatching strategy!')
        raise Exception('Error: Order pool only available with token-passing dispatching strategy!')


def service_set_reserved_nodes(request_body: ReservedNodeRequest):
    if config.config_file.TASK_ASSIGNMENT_STRATEGY == data.enums.TaskAssignmentStrategy.central:
        dispatcher = logic.core.task_assignment_init.task_assignment_strategies[config.config_file.TASK_ASSIGNMENT_STRATEGY]
        return dispatcher.set_reserved_nodes(request_body.amrId, request_body.nodes)
    else:
        logger.exception('Error: Path information only need with central dispatching strategy!')
        raise Exception('Error: Path information only need with central dispatching strategy!')