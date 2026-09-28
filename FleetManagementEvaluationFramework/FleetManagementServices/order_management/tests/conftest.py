import pytest

from database.reset_database import reset_database


@pytest.fixture()
def order_management_db_mock():
    reset_database()
    return
