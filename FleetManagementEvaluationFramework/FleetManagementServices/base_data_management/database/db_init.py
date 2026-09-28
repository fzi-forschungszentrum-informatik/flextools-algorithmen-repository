import os

from api.api_config import app
from api.client_api import reset_database_api_call
from config.config_file import LOAD_LAST_STATUS, DATABASE_FILE
from database.models.db_base_data_models import BaseDataManagement
from database.setup_initial_db import setup_db_with_initial_data, Session  #import of Session important


@app.on_event("startup")
def startup_initialize_event():
    if LOAD_LAST_STATUS is True and DATABASE_FILE != 'sqlite:///:memory:':
        if check_db_is_empty() is False:
            pass
        else:
            setup_db_with_initial_data(os.environ['BASE_DATA_FILE'])
    else:
        if DATABASE_FILE == 'sqlite:///:memory:':  # in in-memory mode, database must not be reset
            setup_db_with_initial_data(os.environ['BASE_DATA_FILE'])
        else:
            reset_database_api_call()


def check_db_is_empty():
    with Session() as session:
        object = session.query(BaseDataManagement).first()
        if object is None:
            return True
        else:
            return False

