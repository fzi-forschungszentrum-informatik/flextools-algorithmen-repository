import pytest

from config.config_file import BASE_DATA_FILE_TEST
from database.reset_database import reset_database


@pytest.fixture()
def base_data_management_mock():
    reset_database(BASE_DATA_FILE_TEST)
    return
