from api.server_api_models import AMRBaseDataRequest
from database.db_init import Session
from database.models.db_base_data_models import PhysicalParameters


def get_amr_data_from_db(request_body: AMRBaseDataRequest):
    with Session() as session:
        if request_body.amrIds[0] == '*':
            amr_physical_data = session.query(PhysicalParameters.speed_max,
                                              PhysicalParameters.acceleration_max,
                                              PhysicalParameters.deceleration_max).all()
        else:
            amr_physical_data = session.query(PhysicalParameters.speed_max,
                                              PhysicalParameters.acceleration_max,
                                              PhysicalParameters.deceleration_max).filter(
                PhysicalParameters.amr_id.in_(request_body.amrIds)).all()

    return amr_physical_data
