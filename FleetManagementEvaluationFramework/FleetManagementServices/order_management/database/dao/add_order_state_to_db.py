from data.models import OrderState
from database.models.db_order_management_models import OrderManagement, OrderInfo, Dimension, PossibleAMRs, Order, \
    Node, NodePosition, Action, ActionParameter, Edge, Trajectory, KnotVector, ControlPoint
from database.db_init import Session


def add_order_state_to_db(request_body: OrderState):
    order_management_data = OrderManagement(order_id=request_body.order.orderId,
                                            amr_id=request_body.amrId,
                                            estimated_start_time=request_body.estimatedStartTime,
                                            estimated_end_time=request_body.estimatedEndTime)
    order_management_data.order_info = OrderInfo(source_id=request_body.newOrderInfo.sourceId,
                                                 sink_id=request_body.newOrderInfo.sinkId,
                                                 start_time=request_body.newOrderInfo.startTime,
                                                 due_time=request_body.newOrderInfo.dueTime,
                                                 item_sku_id=request_body.newOrderInfo.itemSkuId,
                                                 layout_id=request_body.newOrderInfo.layoutId,
                                                 pickup_time=request_body.newOrderInfo.pickupTime,
                                                 dropoff_time=request_body.newOrderInfo.dropoffTime,
                                                 priority=request_body.newOrderInfo.priority,
                                                 status=request_body.newOrderInfo.status)
    if request_body.newOrderInfo.dimension is not None:
        order_management_data.order_info.dimension = Dimension(x=request_body.newOrderInfo.dimension.x,
                                                               y=request_body.newOrderInfo.dimension.y,
                                                               z=request_body.newOrderInfo.dimension.z,
                                                               weight=request_body.newOrderInfo.dimension.weight)
    possible_amr_list = []
    if request_body.newOrderInfo.amrIds is not None:
        for amr_id in request_body.newOrderInfo.amrIds:
            possible_amr_list.append(PossibleAMRs(amr_id=amr_id))
    order_management_data.order_info.amr_ids = possible_amr_list
    order_management_data.order = Order(order_update_id=request_body.order.orderUpdateId,
                                        zone_set_id=request_body.order.zoneSetId)
    node_list = []
    if request_body.order.nodes is not None:
        for node in request_body.order.nodes:
            action_list = []
            if node.actions is not None:
                for action in node.actions:
                    action_parameter_list = []
                    if action.actionParameters is not None:
                        for par in action.actionParameters:
                            action_parameter_list.append(ActionParameter(key=par.key, value=par.value))
                    action_list.append(Action(action_id=action.actionId, action_type=action.actionType,
                                              action_description=action.actionDescription, blocking_type=action.blockingType,
                                              action_parameters=action_parameter_list))
            if node.nodePosition is not None:
                node_position = NodePosition(x=node.nodePosition.x,
                                             y=node.nodePosition.y,
                                             map_id=node.nodePosition.mapId)
            else:
                node_position = None
            node_list.append(Node(node_id=node.nodeId,
                                  sequence_id=node.sequenceId,
                                  released=node.released,
                                  node_position=node_position,
                                  actions=action_list))
    order_management_data.order.nodes = node_list
    edge_list = []
    if request_body.order.edges is not None:
        for edge in request_body.order.edges:
            action_list = []
            if edge.actions is not None:
                for action in edge.actions:
                    action_parameter_list = []
                    if action.actionParameters is not None:
                        for par in action.actionParameters:
                            action_parameter_list.append(ActionParameter(key=par.key, value=par.value))
                    action_list.append(Action(action_id=action.actionId, action_type=action.actionType,
                                              action_description=action.actionDescription,
                                              blocking_type=action.blockingType,
                                              action_parameters=action_parameter_list))
            knot_vector_list = []
            if edge.trajectory.knotVector is not None:
                for value in edge.trajectory.knotVector:
                    knot_vector_list.append(KnotVector(value=value))
            control_point_list = []
            if edge.trajectory.controlPoints is not None:
                for point in edge.trajectory.controlPoints:
                    control_point_list.append(ControlPoint(x= point.x, y=point.y, weight=point.weight))
            trajectory = Trajectory(degree=edge.trajectory.degree, knot_vector=knot_vector_list,
                                    control_points=control_point_list )
            edge_list.append(Edge(edge_id=edge.edgeId, sequence_id=edge.sequenceId, edge_description=edge.edgeDescription,
                                  released=edge.released, start_node_id=edge.startNodeId, end_node_id=edge.endNodeId,
                                  max_speed=edge.maxSpeed, max_height=edge.maxHeight, min_height=edge.minHeight,
                                  orientation=edge.orientation, orientation_type=edge.orientationType,
                                  direction=edge.direction, rotation_allowed=edge.rotationAllowed,
                                  max_rotation_speed=edge.maxRotationSpeed, length=edge.length,
                                  trajectory=trajectory, actions=action_list))

    order_management_data.order.edges = edge_list

    with Session() as session:
        session.add(order_management_data)
        session.commit()

    return
