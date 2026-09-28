from api.client_api import get_items_from_storage_location_tracking, remove_item_from_storage_location_tracking, \
    get_skus_from_storage_location_tracking, remove_skus_from_storage_location_tracking, \
    get_records_from_storage_location_tracking, remove_records_from_storage_location_tracking


def reset_storage_location_tracking():
    """
    :return: Method to reset storage location tracking, if activated
    """
    item_list = get_items_from_storage_location_tracking().json()
    for item in item_list:
        remove_item_from_storage_location_tracking(item['id'])
    sku_list = get_skus_from_storage_location_tracking().json()
    for sku in sku_list:
        remove_skus_from_storage_location_tracking(sku['skuId'])
    record_list = get_records_from_storage_location_tracking().json()
    for record in record_list:
        remove_records_from_storage_location_tracking(record['id'])
    return

