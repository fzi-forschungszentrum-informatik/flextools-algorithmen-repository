from api.client_api_models import OrderUpdateResponse
from api.server_api_models import RepositionOrder
from data.enums import BlockingType, OrderStatus
from data.models import NewOrderInfo, Order, Node, Action, OrderState, NodePosition, Edge


def transform_new_order(new_order: NewOrderInfo, order_update: OrderUpdateResponse) -> OrderState:
    node_list = []

    for node in order_update['order']['nodes']:
        action_list = []
        for action in node['actions']:
            action_list.append(Action(actionId=action['actionId'], actionType=action['actionType'],
                                      blockingType=BlockingType.HARD))
        node_list.append(Node(nodeId=node['nodeId'], sequenceId=node['sequenceId'], released=node['released'],
                              nodePosition=NodePosition(x=node['nodePosition']['x'], y=node['nodePosition']['y'],
                                                        mapId=node['nodePosition']['mapId']),
                              actions=action_list))
    edge_list = []
    for edge in order_update['order']['edges']:
        action_list = []
        for action in edge['actions']:
            action_list.append(Action(actionId=action['actionId'], actionType=action['actionType'],
                                      blockingType=BlockingType.HARD))
        edge_list.append(Edge(edgeId=edge['edgeId'], sequenceId=edge['sequenceId'], released=edge['released'],
                              startNodeId=edge['startNodeId'], endNodeId=edge['endNodeId'],
                              maxSpeed=edge['maxSpeed'], length=edge['length'], actions=action_list))

    order = Order(orderId=order_update['order']['orderId'], orderUpdateId=order_update['order']['orderUpdateId'],
                  nodes=node_list, edges=edge_list)
    new_order.status = OrderStatus.PLANNED
    order_state = OrderState(newOrderInfo=new_order, order=order, amrId=order_update['amrId'],
                             estimatedStartTime=order_update['estimatedStartTime'],
                             estimatedEndTime=order_update['estimatedEndTime'])

    return order_state


def transform_reposition_order(reposition_order: RepositionOrder):
    order_info = NewOrderInfo(orderId=reposition_order.order.orderId,
                              sourceId=reposition_order.order.nodes[0].nodeId,
                              sinkId=reposition_order.order.nodes[-1].nodeId,
                              status=OrderStatus.PLANNED)
    order_state = OrderState(newOrderInfo=order_info, order=reposition_order.order,
                             amrId=reposition_order.amrId)
    return order_state
