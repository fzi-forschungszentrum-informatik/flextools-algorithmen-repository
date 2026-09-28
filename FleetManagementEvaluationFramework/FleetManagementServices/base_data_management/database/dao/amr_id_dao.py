from api.server_api_models import AmrPropertyRequest
from database.db_init import Session
from database.models.db_base_data_models import LoadDimension, LoadSpecification, BaseDataManagement
from sqlalchemy import and_


def get_possible_amr_ids_by_dimension_request(request_body: AmrPropertyRequest):
    with Session() as session:
        amr_ids = session.query(LoadSpecification.amr_id).join(LoadDimension,
                                                               LoadSpecification.load_specification_id ==
                                                               LoadDimension.load_specification_id).filter(
            and_(LoadDimension.length >= request_body.x,
                 LoadDimension.width >= request_body.y,
                 LoadDimension.height >= request_body.z,
                 LoadSpecification.max_weight >= request_body.weight)).all()
    rel_amr_ids = [_id[0] for _id in amr_ids]
    return rel_amr_ids


def get_all_amr_ids():
    with Session() as session:
        amr_ids = session.query(BaseDataManagement.amr_id).all()
    amr_ids = [_id[0] for _id in amr_ids]
    return amr_ids

