from flask import request
from flask_restx import Namespace, Resource, fields
from flask_restx.inputs import datetime_from_iso8601
from storage_location_tracking.models import db, InventoryHistory
from .api import request_wrapper


api_namespace = Namespace('inventory')

inventory_history_model = api_namespace.model('InventoryHistory', {
    'id': fields.String(description='The unique identifier of the inventory history record', readonly=True),
    'item_id': fields.String(description='The ID of the item associated with this inventory history record', readonly=True),
    'item_number': fields.String(description='The item number of the item associated with this inventory history record', readonly=True),
    'quantity': fields.Integer(description='The quantity of the item at the given timestamp', readonly=True),
    'timestamp': fields.DateTime(description='The timestamp when the quantity was recorded', readonly=True),
})

@api_namespace.route('/', endpoint='inventory', methods=['GET'])
class InventoryResource(Resource):
    @api_namespace.expect(
        api_namespace.parser().add_argument('id', type=str, required=False, help='The ID of the inventory record', location='args'), 
        api_namespace.parser().add_argument('item_id', type=str, required=False, help='The ID of the item you want to have inventory records of', location='args'), 
        api_namespace.parser().add_argument('item_number', type=str, required=False, help='The item number of the item you want to have inventory records of', location='args'),
        api_namespace.parser().add_argument('timestamp', type=datetime_from_iso8601, required=False, help='The timestamp of the inventory records', location='args'))
    @api_namespace.marshal_list_with(inventory_history_model)
    @request_wrapper
    def get(self):
        id = request.args.get('id', False)
        item_id = request.args.get('item_id', False)
        item_number = request.args.get('item_number', False)
        timestamp = request.args.get('timestamp', False)
        records = InventoryHistory.query_inventory_history(id, item_id, item_number, timestamp)
        if type(records) is not list:
            return records.to_dict()
        return [record.to_dict() for record in records]