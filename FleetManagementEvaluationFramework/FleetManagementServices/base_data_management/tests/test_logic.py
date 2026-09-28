from api.server_api_models import AmrPropertyRequest
from logic.services import service_get_amrs_with_specific_properties, service_get_all_amrs


def test_service_get_amrs_with_specific_properties(base_data_management_mock):
    amr_property_request = AmrPropertyRequest(x=45, y=45, z=20, weight=1.2)
    response = service_get_amrs_with_specific_properties(amr_property_request)
    assert response[0] == '3'


def test_service_get_all_amrs(base_data_management_mock):
    response = service_get_all_amrs()
    assert response == ['1', '2', '3']
