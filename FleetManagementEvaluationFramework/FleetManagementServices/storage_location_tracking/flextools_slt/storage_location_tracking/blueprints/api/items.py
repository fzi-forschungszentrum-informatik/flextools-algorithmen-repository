from flask import request
from flask_restx import Namespace, Resource, fields, reqparse
from storage_location_tracking.models import db, Item, UL, ULRecord, Location, batch_compute_quantities
from .api import request_wrapper



api_namespace = Namespace('items')

item_model = api_namespace.model('Item', {
    'id': fields.String(description='The unique identifier of the item', readonly=True),
    'number': fields.String(description='The unique number of the item'),
    'description': fields.String(description='The description of the item'),
    'quantity': fields.Integer(description='The quantity of the item', readonly=True),
    'weight': fields.Float(description='The weight of the item', nullable=True),
    'height': fields.Float(description='The height of the item', nullable=True),
    'width': fields.Float(description='The width of the item', nullable=True),
    'length': fields.Float(description='The length of the item', nullable=True),
})
parser = reqparse.RequestParser()
parser.add_argument('id', type=str, required=False, help='Item ID', location='args')
parser.add_argument('number', type=int, required=False, help='Item Number', location='args')
parser.add_argument('page', type=int, default=1, help='Page number', location='args')
parser.add_argument('per_page', type=int, default=20, help='Items per page', location='args')

@api_namespace.route('/', endpoint='items', methods=['GET', 'POST', 'PATCH', 'DELETE'])
class ItemsResource(Resource):
    @api_namespace.expect(parser)
    @api_namespace.marshal_list_with(item_model)
    @request_wrapper
    def get(self):
        args = parser.parse_args()
        id = args.get('id')
        number = args.get('number')
        page = args['page']
        per_page = args['per_page']

        if id:  
            item = Item.query.filter_by(id=id).first_or_404()
            return item.to_dict()
        elif number:
            item = Item.query.filter_by(number=number).first()
            return item.to_dict()
        else:
            items = Item.query.paginate(page=page, per_page=per_page, error_out=False)
            batch_compute_quantities(items.items)
            return [item.to_dict() for item in items.items]
    
    @api_namespace.expect(item_model)
    @api_namespace.marshal_list_with(item_model)
    @request_wrapper
    def post(self):
        data = request.get_json()
        new_item = Item(**data)
        db.session.add(new_item)
        db.session.commit()
        return Item.query.get_or_404(new_item.id).to_dict()

    @api_namespace.expect(
            api_namespace.parser().add_argument('id', type=str, required=False, help='The ID of the Item', location='args'),
            api_namespace.parser().add_argument('number', type=int, required=False, help='The Number of the Item', location='args'), 
            item_model)
    @api_namespace.marshal_list_with(item_model)
    @request_wrapper
    def patch(self):
        if request.args.get('id'):
            id = request.args.get('id')
            item = Item.query.get_or_404(id)
        elif request.args.get('number'):
            number = request.args.get('number')
            item = Item.query.filter_by(number=number).first()
        data = request.get_json()
        for key, value in data.items():
            if key in item.__dict__: 
                setattr(item, key, value)
        db.session.commit()
        return Item.query.get_or_404(item.id).to_dict()

    @api_namespace.expect(
            api_namespace.parser().add_argument('id', type=str, required=False, help='The ID of the Item', location='args'), 
            api_namespace.parser().add_argument('number', type=int, required=False, help='The Number of the Item', location='args'))
    def delete(self):
        if request.args.get('id'):
            id = request.args.get('id')
            item = Item.query.get_or_404(id)
        elif request.args.get('number'):
            number = request.args.get('number')
            item = Item.query.filter_by(number=number).first()
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item deleted successfully"}