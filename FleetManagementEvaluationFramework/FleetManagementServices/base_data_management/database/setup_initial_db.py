import json

from data.enums import AGVKinematic, AGVClass, LocalizationType, NavigationType, ParameterSupport, ActionScope
from database.models.db_base_data_models import TypeSpecification, LocalizationTypeDb, BaseDataManagement, \
    NavigationTypeDb, PhysicalParameters, ProtocolFeatures, OptionalParameters, ActionScopesDb, LoadSpecification, \
    LoadDimension, AGVActions

from database.db import engine
from database.models.db_base_data_models import Base
from sqlalchemy.orm import sessionmaker


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def setup_db_with_initial_data(file: str):
    if file == '':
        return
    f = open(file, "r")
    data = json.load(f)
    f.close()

    for item in data:
        amr_base_data = BaseDataManagement(amr_id=item['amr_id'])
        amr_base_data.type_specification = TypeSpecification(series_name=item['type_specification']['series_name'],
                                                             agv_kinematic=AGVKinematic(item['type_specification']
                                                                                        ['agv_kinematic']),
                                                             agv_class=AGVClass(item['type_specification']
                                                                                ['agv_class']),
                                                             max_load_mass=item['type_specification']['max_load_mass'])
        for loc in item['type_specification']['localization_types']:
            amr_base_data.type_specification.localization_types.append(LocalizationTypeDb(localization_type=
                                                                                          LocalizationType(loc)))
        for nav in item['type_specification']['navigation_types']:
            amr_base_data.type_specification.navigation_types.append(NavigationTypeDb(navigation_type=
                                                                                      NavigationType(nav)))
        amr_base_data.physical_parameters = PhysicalParameters(speed_min=item['physical_parameters']['speed_min'],
                                                               speed_max=item['physical_parameters']['speed_max'],
                                                               acceleration_max=item['physical_parameters'][
                                                                   'acceleration_max'],
                                                               deceleration_max=item['physical_parameters'][
                                                                   'deceleration_max'],
                                                               height_max=item['physical_parameters']['height_max'],
                                                               width=item['physical_parameters']['width'],
                                                               length=item['physical_parameters']['length'])
        amr_base_data.protocol_features = ProtocolFeatures()
        for opt in item['protocol_features']['optional_parameters']:
            amr_base_data.protocol_features.optional_parameters.append(OptionalParameters(parameter=opt['parameter'],
                                                                                          support=ParameterSupport(
                                                                                              opt['support'])))
        for act in item['protocol_features']['agv_actions']:
            action_scopes_list = []
            for sco in act['action_scopes']:
                action_scopes_list.append(ActionScopesDb(action_scope=ActionScope(sco)))
            amr_base_data.protocol_features.agv_actions.append(AGVActions(action_type=act['action_type'],
                                                                          action_scopes=action_scopes_list))

        amr_base_data.load_specification = LoadSpecification(max_weight=item['load_specification']['max_weight'])
        amr_base_data.load_specification.load_dimensions = LoadDimension(length=item['load_specification']
                                                                         ['load_dimension']['length'],
                                                                         width=item['load_specification']
                                                                         ['load_dimension']['width'],
                                                                         height=item['load_specification']
                                                                         ['load_dimension']['height'])

        with Session() as session:
            session.add(amr_base_data)
            session.commit()

    return
