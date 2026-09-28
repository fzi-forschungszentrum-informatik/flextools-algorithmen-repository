from api.api_config import app

from api.server_api_models import (NewOrderInfo, DispatchingStrategy, RequestOrderAMR, DeleteOrderRequest,
                                   ReleaseOrderRequest, ReservedNodeRequest)
from logic.api_services.services import (service_dispatch_new_order, service_set_dispatching_strategy,
                                         service_get_order_from_order_pool, service_delete_order_from_order_pool,
                                         service_reset_dispatching, service_release_order_in_order_pool, service_set_reserved_nodes)


######################
# Rest-API Endpoints #
######################
@app.post("/new-order")
async def get_new_order_request(request_body: NewOrderInfo):
    return service_dispatch_new_order(request_body)


@app.put("/dispatching-strategy")
async def set_dispatching_strategy_request(request_body: DispatchingStrategy):
    return service_set_dispatching_strategy(request_body)


@app.get("/order-from-order-pool")
async def request_order_from_order_pool(request_body: RequestOrderAMR):
    res = service_get_order_from_order_pool(request_body)
    return res


@app.delete("/delete-order-from-order-pool")
async def delete_order_from_order_pool(request_body: DeleteOrderRequest):
    res = service_delete_order_from_order_pool(request_body)
    return res


@app.post("/reset")
async def reset_dispatching():
    return service_reset_dispatching()


@app.post("/release-order-in-order-pool")
async def release_order_in_order_pool(request_body: ReleaseOrderRequest):
    return service_release_order_in_order_pool(request_body)


@app.put("/reserved-nodes-central")
async def set_reserved_nodes_central(request_body: ReservedNodeRequest):
    return service_set_reserved_nodes(request_body)
