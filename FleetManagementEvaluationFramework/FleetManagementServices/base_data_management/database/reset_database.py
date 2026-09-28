from database.db_init import Session
from database.models.db_base_data_models import BaseDataManagement, TypeSpecification, LocalizationTypeDb, \
    NavigationTypeDb, PhysicalParameters, ProtocolFeatures, OptionalParameters, AGVActions, ActionScopesDb, \
    LoadSpecification, LoadPosition, LoadDimension
from database.setup_initial_db import setup_db_with_initial_data


def reset_database(file_new_database_input: str):
    with Session() as session:
        session.query(BaseDataManagement).delete()
        session.query(TypeSpecification).delete()
        session.query(LocalizationTypeDb).delete()
        session.query(NavigationTypeDb).delete()
        session.query(PhysicalParameters).delete()
        session.query(ProtocolFeatures).delete()
        session.query(OptionalParameters).delete()
        session.query(AGVActions).delete()
        session.query(ActionScopesDb).delete()
        session.query(LoadSpecification).delete()
        session.query(LoadPosition).delete()
        session.query(LoadDimension).delete()
        session.commit()
    setup_db_with_initial_data(file_new_database_input)
    return
