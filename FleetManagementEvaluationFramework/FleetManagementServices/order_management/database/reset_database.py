from database.db_init import Session
from database.models.db_order_management_models import OrderManagement, OrderInfo, PossibleAMRs, Dimension, Order, \
    Node, NodePosition, Action, ActionParameter, Edge, Trajectory, KnotVector, ControlPoint


def reset_database():
    # order database initial empty, no orders
    with Session() as session:
        session.query(OrderManagement).delete()
        session.query(OrderInfo).delete()
        session.query(PossibleAMRs).delete()
        session.query(Dimension).delete()
        session.query(Order).delete()
        session.query(Node).delete()
        session.query(NodePosition).delete()
        session.query(Action).delete()
        session.query(ActionParameter).delete()
        session.query(Edge).delete()
        session.query(Trajectory).delete()
        session.query(KnotVector).delete()
        session.query(ControlPoint).delete()
        session.commit()
    return

