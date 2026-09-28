from api.api_config import app
from api.server_api_models import AmrPropertyRequest, AMRBaseDataRequest, PathRequest
from data.models import NewAMRRequest
from logic.services import service_get_amrs_with_specific_properties, service_get_all_amrs, service_add_new_amr, \
    service_get_amr_data, service_reset_base_data_management, service_set_base_data_file_new


######################
# Rest-API Endpoints #
######################
@app.get("/possible-amrs")
async def amr_property_request(request_body: AmrPropertyRequest):
    return service_get_amrs_with_specific_properties(request_body)


@app.get("/all-amrs")
async def amr_property_request():
    return service_get_all_amrs()


@app.post("/new-amr")
async def add_new_amr_request(request_body: NewAMRRequest):
    return service_add_new_amr(request_body)


@app.get("/base-data")
async def get_amr_data(request_body: AMRBaseDataRequest):
    return service_get_amr_data(request_body)


@app.post("/reset")
async def reset_base_data_management():
    return service_reset_base_data_management()


@app.get('/health')
async def health():
    return


@app.post("/set-base-data-file")
async def set_base_data_file_new(request_body: PathRequest):
    service_set_base_data_file_new(request_body)
