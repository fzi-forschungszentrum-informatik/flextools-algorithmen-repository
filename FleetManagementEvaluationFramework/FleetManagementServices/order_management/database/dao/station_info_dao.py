from api.server_api_models import StationInfoRequest
from database.db_init import Session
from database.models.db_order_management_models import OrderInfo


def get_station_ids_for_order_from_db(request_body: StationInfoRequest):
    with Session() as session:
        stations = session.query(OrderInfo.source_id,
                                 OrderInfo.sink_id).filter(OrderInfo.order_id == request_body.orderId).first()
    return stations
