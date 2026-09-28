from data.enums import AGVKinematic, AGVClass, LocalizationType, NavigationType, ActionScope, ParameterSupport
from database.db import Base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship


class BaseDataManagement(Base):
    __tablename__ = 'db_base_data'

    amr_id = Column(String, primary_key=True, unique=True)
    type_specification = relationship('TypeSpecification',
                                      uselist=False,
                                      single_parent=True,
                                      backref='db_base_data')
    physical_parameters = relationship('PhysicalParameters',
                                       uselist=False,
                                       single_parent=True,
                                       backref='db_base_data')
    protocol_features = relationship('ProtocolFeatures',
                                     uselist=False,
                                     single_parent=True,
                                     backref='db_base_data')
    load_specification = relationship('LoadSpecification',
                                      uselist=False,
                                      single_parent=True,
                                      backref='db_base_data')


class TypeSpecification(Base):
    __tablename__ = 'type_specification'

    type_specification_id = Column(Integer, primary_key=True, autoincrement=True)
    series_name = Column(String, nullable=False)
    agv_kinematic = Column(Enum(AGVKinematic), nullable=False)
    agv_class = Column(Enum(AGVClass), nullable=False)
    max_load_mass = Column(Float, nullable=False)
    localization_types = relationship('LocalizationTypeDb',
                                      backref='type_specification')
    navigation_types = relationship('NavigationTypeDb',
                                    backref='type_specification')
    amr_id = Column(String, ForeignKey('db_base_data.amr_id'))


class LocalizationTypeDb(Base):
    __tablename__ = 'localization_type'

    localization_type_id = Column(Integer, primary_key=True, autoincrement=True)
    localization_type = Column(Enum(LocalizationType), nullable=False)
    type_specification_id = Column(Integer, ForeignKey('type_specification.type_specification_id'), nullable=True)


class NavigationTypeDb(Base):
    __tablename__ = 'navigation_type'

    navigation_type_id = Column(Integer, primary_key=True, autoincrement=True)
    navigation_type = Column(Enum(NavigationType), nullable=False)
    type_specification_id = Column(Integer, ForeignKey('type_specification.type_specification_id'), nullable=True)


class PhysicalParameters(Base):
    __tablename__ = 'physical_parameters'

    physical_parameter_id = Column(Integer, primary_key=True, autoincrement=True)
    speed_min = Column(Float, nullable=False)
    speed_max = Column(Float, nullable=False)
    acceleration_max = Column(Float, nullable=False)
    deceleration_max = Column(Float, nullable=False)
    height_min = Column(Float, nullable=True)
    height_max = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    length = Column(Float, nullable=False)
    amr_id = Column(String, ForeignKey('db_base_data.amr_id'), nullable=False)


class ProtocolFeatures(Base):
    __tablename__ = 'protocol_features'

    protocol_feature_id = Column(Integer, primary_key=True, autoincrement=True)
    optional_parameters = relationship('OptionalParameters',
                                       backref='protocol_features')
    agv_actions = relationship('AGVActions',
                                backref='protocol_features')
    amr_id = Column(String, ForeignKey('db_base_data.amr_id'))


class OptionalParameters(Base):
    __tablename__ = 'optional_parameters'

    optional_parameter_id = Column(Integer, primary_key=True, autoincrement=True)
    parameter = Column(String, nullable=False)
    support = Column(Enum(ParameterSupport), nullable=False)
    protocol_feature_id = Column(Integer, ForeignKey('protocol_features.protocol_feature_id'), nullable=True)


class AGVActions(Base):
    __tablename__ = 'agv_actions'

    agv_action_id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String, nullable=False)
    action_scopes = relationship('ActionScopesDb',
                                 backref='agv_actions')
    protocol_feature_id = Column(Integer, ForeignKey('protocol_features.protocol_feature_id'), nullable=True)


class ActionScopesDb(Base):
    __tablename__ = 'action_scopes'

    action_scope_id = Column(Integer, primary_key=True, autoincrement=True)
    action_scope = Column(Enum(ActionScope), nullable=False)
    agv_action_id = Column(Integer, ForeignKey('agv_actions.agv_action_id'), nullable=True)


class LoadSpecification(Base):
    __tablename__ = 'load_specification'

    load_specification_id = Column(Integer, primary_key=True, autoincrement=True)
    load_positions = relationship('LoadPosition',
                                  backref='load_specification')
    load_dimensions = relationship('LoadDimension',
                                   uselist=False,
                                   single_parent=True,
                                   backref='load_specification')
    max_weight = Column(Float, nullable=True)
    agv_speed_limit = Column(Float, nullable=True)
    agv_acceleration_limit = Column(Float, nullable=True)
    agv_deceleration_limit = Column(Float, nullable=True)
    pick_time = Column(Float, nullable=True)
    drop_time = Column(Float, nullable=True)
    amr_id = Column(String, ForeignKey('db_base_data.amr_id'), nullable=False)


class LoadPosition(Base):
    __tablename__ = 'load_position'

    load_position_id = Column(Integer, primary_key=True, autoincrement=True)
    load_position = Column(String, nullable=False)
    load_specification_id = Column(Integer, ForeignKey('load_specification.load_specification_id'), nullable=True)


class LoadDimension(Base):
    __tablename__ = 'load_dimension'

    load_dimension_id = Column(Integer, primary_key=True, autoincrement=True)
    length = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=True)
    load_specification_id = Column(Integer, ForeignKey('load_specification.load_specification_id'), nullable=True)


