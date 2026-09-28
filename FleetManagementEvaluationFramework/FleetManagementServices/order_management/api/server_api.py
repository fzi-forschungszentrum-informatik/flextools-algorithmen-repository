from api.api_config import app
from api.server_api_models import OrderUpdateRequest, OrderInfoRequest, SetSKURequest, StationInfoRequest, \
    RepositionOrder
from data.models import NewOrderInfo
from logic.services import service_get_new_order, service_set_order_update, service_get_order_infos, \
    service_reset_order_database, service_get_item_sku_info, service_set_item_sku_info, service_get_last_order_status, \
    service_get_locations_for_order, service_set_reposition_order


######################
# Rest-API Endpoints #
######################

@app.post("/new-order")
async def get_new_order_request(request_body: NewOrderInfo):
    return service_get_new_order(request_body)


@app.put("/order-update")
async def set_order_update_request(request_body: OrderUpdateRequest):
    return service_set_order_update(request_body)


@app.get("/order-infos")
async def get_order_infos_request(request_body: OrderInfoRequest):
    return service_get_order_infos(request_body)


@app.post("/reset")
async def reset_order_management():
    return service_reset_order_database()


@app.get('/health')
async def health():
    # print('Health endpoint')
    return


@app.get('/item-sku-info')
async def get_item_sku_info(request_body: OrderInfoRequest):
    return service_get_item_sku_info(request_body)


@app.put('/item-sku-info')
async def set_item_sku_info(request_body: SetSKURequest):
    return service_set_item_sku_info(request_body)


@app.get('/last-order-status')
async def get_last_order_status(request_body: OrderInfoRequest):
    return service_get_last_order_status(request_body)


@app.get('/stations-for-order')
async def get_stations_for_order(request_body: StationInfoRequest):
    return service_get_locations_for_order(request_body)


@app.post('/set-reposition-order')
async def set_reposition_order(request_body: RepositionOrder):
    return service_set_reposition_order(request_body)

