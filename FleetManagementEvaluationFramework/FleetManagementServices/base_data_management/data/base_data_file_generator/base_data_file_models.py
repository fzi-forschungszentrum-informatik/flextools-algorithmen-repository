from typing import List

from pydantic import BaseModel


class TypeSpecification(BaseModel):
    series_name: str = "a_series"
    agv_kinematic: str = "DIFF"
    agv_class: str = "CARRIER"
    max_load_mass: int = 5
    localization_types: List[str] = ["NATURAL", "GRID"]
    navigation_types: List[str] = ["AUTONOMOUS"]


class PhysicalParameters(BaseModel):
    speed_min: float = 0
    speed_max: float = 1
    acceleration_max: float = 2
    deceleration_max: float = 3
    height_max: float = 1.2
    width: float = 50
    length: float = 60


class OptionalParameter(BaseModel):
    parameter: str = "Duration"
    support: str = "SUPPORTED"


class AGVAction(BaseModel):
    action_type: str
    action_scopes: List[str]


class ProtocolFeatures(BaseModel):
    optional_parameters: List[OptionalParameter] = [OptionalParameter()]
    agv_actions: List[AGVAction] = [AGVAction(action_type="PICKUP", action_scopes=["NODE"]),
                                    AGVAction(action_type="DROPOFF", action_scopes=["NODE"])]


class LoadDimension(BaseModel):
    length: float = 40
    width: float = 40
    height: float = 30


class LoadSpecification(BaseModel):
    load_dimension: LoadDimension = LoadDimension()
    max_weight: float = 10


class BaseDataFile(BaseModel):
    amr_id: str
    type_specification: TypeSpecification = TypeSpecification()
    physical_parameters: PhysicalParameters = PhysicalParameters()
    protocol_features: ProtocolFeatures = ProtocolFeatures()
    load_specification: LoadSpecification = LoadSpecification()
