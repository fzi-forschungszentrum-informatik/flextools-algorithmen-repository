from data.enums import AGVKinematic, AGVClass, LocalizationType, NavigationType, ParameterSupport, ActionScope
from data.models import NewAMRRequest
from database.models.db_base_data_models import BaseDataManagement, TypeSpecification, LocalizationTypeDb, \
    NavigationTypeDb, PhysicalParameters, ProtocolFeatures, OptionalParameters, AGVActions, ActionScopesDb, \
    LoadSpecification, LoadDimension
from database.db_init import Session


def add_amr_to_db(request_body: NewAMRRequest):
    amr_base_data = BaseDataManagement(amr_id=request_body.amrId)
    amr_base_data.type_specification = TypeSpecification(series_name=request_body.seriesName,
                                                         agv_kinematic=AGVKinematic.DIFF,
                                                         agv_class=AGVClass(request_body.agvClass),
                                                         max_load_mass=request_body.maxLoadMass)
    amr_base_data.type_specification.localization_types = [LocalizationTypeDb(localization_type=LocalizationType.GRID)]
    amr_base_data.type_specification.navigation_types = [NavigationTypeDb(navigation_type=NavigationType.AUTONOMOUS)]
    amr_base_data.physical_parameters = PhysicalParameters(speed_min=0,
                                                           speed_max=request_body.maxSpeed,
                                                           acceleration_max=2,
                                                           deceleration_max=3,
                                                           height_max=request_body.height,
                                                           width=request_body.width,
                                                           length=request_body.length)
    amr_base_data.protocol_features = ProtocolFeatures()
    amr_base_data.protocol_features.optional_parameters = [OptionalParameters(parameter='Duration',
                                                                              support=ParameterSupport.SUPPORTED)]
    amr_base_data.protocol_features.agv_actions = [AGVActions(action_type='Pickup',
                                                              action_scopes=[ActionScopesDb(
                                                                  action_scope=ActionScope.NODE)]),
                                                   AGVActions(action_type='Dropoff',
                                                              action_scopes=[ActionScopesDb(
                                                                  action_scope=ActionScope.NODE)]),
                                                   ]
    amr_base_data.load_specification = LoadSpecification(max_weight=request_body.maxLoadMass)
    amr_base_data.load_specification.load_dimensions = LoadDimension(length=request_body.loadDimension.length,
                                                                     width=request_body.loadDimension.width,
                                                                     height=request_body.loadDimension.height)

    with Session() as session:
        amr_data = session.query(BaseDataManagement.amr_id).filter(BaseDataManagement.amr_id == request_body.amrId).all()
        if len(amr_data) == 0:
            session.add(amr_base_data)
            session.commit()
    return

