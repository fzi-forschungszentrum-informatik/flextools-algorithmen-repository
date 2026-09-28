from api.api_config import app
from api.client_api import reset_database_api_call
from config.config_file import LOAD_LAST_STATUS, DATABASE_FILE

from database.db import engine
from database.models.db_order_management_models import Base, OrderManagement
from sqlalchemy.orm import sessionmaker


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


@app.on_event("startup")
def startup_initialize_event():
    if LOAD_LAST_STATUS is True and DATABASE_FILE != 'sqlite:///:memory:':
        pass  # Nothing to do, database initial empty
    else:
        if DATABASE_FILE == 'sqlite:///:memory:':  # in in-memory mode, database must not be reset
            pass  # Nothing to do, database initial empty
        else:
            reset_database_api_call()


def check_db_is_empty():
    with Session() as session:
        object = session.query(OrderManagement).first()
        if object is None:
            return True
        else:
            return False
