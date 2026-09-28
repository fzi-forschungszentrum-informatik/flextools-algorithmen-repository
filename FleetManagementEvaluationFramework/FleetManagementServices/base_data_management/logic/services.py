import os
import logging

import config.config_file
from api.server_api_models import AmrPropertyRequest, AMRBaseDataRequest, PathRequest
from data.models import NewAMRRequest
from database.dao.add_amr_to_db import add_amr_to_db
from database.dao.amr_data_dao import get_amr_data_from_db
from database.dao.amr_id_dao import get_possible_amr_ids_by_dimension_request, get_all_amr_ids
from database.reset_database import reset_database
from database.transformations.transformations_to_api import transform_amr_physical_data_to_api_obj

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def service_get_amrs_with_specific_properties(request_body: AmrPropertyRequest):
    possible_amrs = get_possible_amr_ids_by_dimension_request(request_body)
    logger.debug(f'Possible AMRs: {possible_amrs}')
    return possible_amrs


def service_get_all_amrs():
    return get_all_amr_ids()


def service_add_new_amr(request_body: NewAMRRequest):
    add_amr_to_db(request_body)
    return


def service_get_amr_data(request_body: AMRBaseDataRequest):
    amr_physical_data = get_amr_data_from_db(request_body)
    response = transform_amr_physical_data_to_api_obj(amr_physical_data)
    return response


def service_reset_base_data_management():
    reset_database(os.environ['BASE_DATA_FILE'])
    return


def service_set_base_data_file_new(request_body: PathRequest):
    reset_database(request_body.path)
    return
