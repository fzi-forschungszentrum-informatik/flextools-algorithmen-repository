from data.enums import OrderStatus, BlockingType
from database.db import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime, Boolean, JSON, Table
from sqlalchemy.orm import relationship


class OrderManagement(Base):
    __tablename__ = 'db_order_management'

    order_id = Column(String, primary_key=True, unique=True)
    order_info = relationship('OrderInfo',
                              uselist=False,
                              single_parent=True,
                              backref='db_order_management')
    order = relationship('Order',
                         uselist=False,
                         single_parent=True,
                         backref='db_order_management')
    amr_id = Column(String, nullable=True)
    estimated_start_time = Column(DateTime, nullable=True)
    estimated_end_time = Column(DateTime, nullable=True)


class OrderInfo(Base):
    __tablename__ = 'order_info'

    order_id = Column(String, ForeignKey('db_order_management.order_id'), primary_key=True, unique=True)
    source_id = Column(String, nullable=True)
    sink_id = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=True)
    due_time = Column(DateTime, nullable=True)
    dimension = relationship('Dimension',
                             uselist=False,
                             single_parent=True,
                             backref='order_info')
    item_sku_id = Column(String, nullable=True)
    layout_id = Column(String, nullable=True)
    pickup_time = Column(Integer, nullable=True)
    dropoff_time = Column(Integer, nullable=True)
    priority = Column(Integer, nullable=True)
    amr_ids = relationship('PossibleAMRs',
                           backref='order_info')
    status = Column(Enum(OrderStatus), nullable=False)


class PossibleAMRs(Base):
    __tablename__ = 'possible_amrs'

    amr_id_index = Column(Integer, primary_key=True, autoincrement=True)
    amr_id = Column(String, nullable=False)
    order_id = Column(String, ForeignKey('order_info.order_id'), nullable=True)


class Dimension(Base):
    __tablename__ = 'dimension'

    dimension_id = Column(Integer, primary_key=True, autoincrement=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    order_id = Column(String, ForeignKey('order_info.order_id'), nullable=True)


class Action(Base):
    __tablename__ = 'actions'

    action_id = Column(String, primary_key=True, unique=True)
    action_type = Column(String, nullable=False)
    action_description = Column(String, nullable=True)
    blocking_type = Column(Enum(BlockingType), nullable=False)
    action_parameters = relationship('ActionParameter', backref='actions')


class ActionParameter(Base):
    __tablename__ = 'action_parameter'

    action_parameter_id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, nullable=False)
    value = Column(JSON, nullable=False)
    action_id = Column(String, ForeignKey('actions.action_id'), nullable=True)


class Node(Base):
    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String, nullable=False)
    sequence_id = Column(Integer, nullable=False)
    node_description = Column(String, nullable=True)
    released = Column(Boolean, nullable=False)
    node_position = relationship('NodePosition',
                                 uselist=False,
                                 single_parent=True,
                                 backref='nodes')
    actions = relationship('Action', back_populates='node')


Action.node_id = Column(Integer, ForeignKey('nodes.id'), nullable=True)


class NodePosition(Base):
    __tablename__ = 'node_position'

    node_position_id = Column(Integer, primary_key=True, autoincrement=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    theta = Column(Float, nullable=True)
    map_id = Column(String, nullable=False)
    node_id = Column(String, ForeignKey('nodes.node_id'), nullable=True)


class Edge(Base):
    __tablename__ = 'edges'

    id = Column(Integer, primary_key=True, autoincrement=True)
    edge_id = Column(String, nullable=False)
    sequence_id = Column(Integer, nullable=False)
    edge_description = Column(String, nullable=True)
    released = Column(Boolean, nullable=False)
    start_node_id = Column(String, nullable=False)
    end_node_id = Column(String, nullable=False)
    max_speed = Column(Float, nullable=True)
    max_height = Column(Float, nullable=True)
    min_height = Column(Float, nullable=True)
    orientation = Column(Float, nullable=True)
    orientation_type = Column(String, nullable=True)
    direction = Column(String, nullable=True)
    rotation_allowed = Column(Boolean, nullable=True)
    max_rotation_speed = Column(Float, nullable=True)
    length = Column(Float, nullable=True)
    trajectory = relationship('Trajectory', uselist=False, single_parent=True, backref='edges')
    actions = relationship('Action', back_populates='edge')
    # order_id = Column(String, ForeignKey('order.order_id'), nullable=True)


Action.edge_id = Column(Integer, ForeignKey('edges.id'), nullable=True)


class Trajectory(Base):
    __tablename__ = 'trajectory'

    trajectory_id = Column(Integer, primary_key=True, autoincrement=True)
    degree = Column(Integer, nullable=False)
    knot_vector = relationship('KnotVector', backref='trajectory')
    control_points = relationship('ControlPoint', backref='trajectory')
    egde_id = Column(String, ForeignKey('edges.edge_id'), nullable=True)


class KnotVector(Base):
    __tablename__ = 'knot_vector'

    knot_vector_id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(Float, nullable=False)
    trajectory_id = Column(Integer, ForeignKey('trajectory.trajectory_id'), nullable=True)


class ControlPoint(Base):
    __tablename__ = 'control_point'

    control_point_id = Column(Integer, primary_key=True, autoincrement=True)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    weight = Column(Float, nullable=True)
    trajectory_id = Column(Integer, ForeignKey('trajectory.trajectory_id'), nullable=True)


class Order(Base):
    __tablename__ = 'orders'

    order_id = Column(String, ForeignKey('db_order_management.order_id'), primary_key=True, unique=True)
    order_update_id = Column(Integer, nullable=False)
    zone_set_id = Column(String, nullable=True)
    nodes = relationship('Node', back_populates='order')
    edges = relationship('Edge', back_populates='order')

Node.order_id = Column(String, ForeignKey('orders.order_id'), nullable=True)
Edge.order_id = Column(String, ForeignKey('orders.order_id'), nullable=True)

Node.order = relationship('Order', back_populates='nodes')
Edge.order = relationship('Order', back_populates='edges')
Action.node = relationship('Node', back_populates='actions')
Action.edge = relationship('Edge', back_populates='actions')
