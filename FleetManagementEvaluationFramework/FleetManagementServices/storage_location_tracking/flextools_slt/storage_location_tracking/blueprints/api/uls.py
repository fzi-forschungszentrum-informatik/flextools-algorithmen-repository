from flask import request 
from flask_restx import Namespace, Resource, fields, reqparse
from sqlalchemy.orm import selectinload
from storage_location_tracking.models import db, UL, ULRecord
import storage_location_tracking.services as services
from .api import request_wrapper
from .ulRecords import ul_record_model


api_namespace = Namespace('uls')

ul_model = api_namespace.model('UL', {
    'ulId': fields.String(description='The unique identifier of the UL', readonly=True),
    'itemId': fields.String(description='The ID of the item associated with the UL'),
    'is_stored': fields.Boolean(description='Indicates whether the UL is currently stored', readonly=True),
    'completly_retrieved': fields.Boolean(description='Indicates whether the UL has been completly retrieved', readonly=True),
    'has_been_stored': fields.Boolean(description='Indicates whether the UL has been stored', readonly=True),
})

parser = reqparse.RequestParser()
parser.add_argument('ulId', type=str, required=False, help='The ID of the UL', location='args')
parser.add_argument('page', type=int, default=1, help='Page number', location='args')
parser.add_argument('per_page', type=int, default=20, help='Items per page', location='args')

@api_namespace.route('/', methods=['GET', 'POST', 'PATCH', 'DELETE'])
class ULsResource(Resource):
    @api_namespace.expect(parser)
    @api_namespace.marshal_list_with(ul_model)
    @request_wrapper
    def get(self):
        args = parser.parse_args()
        ulId = args.get('ulId')
        page = args['page']
        per_page = args['per_page']
        
        if ulId is None:
            uls = UL.query.options(selectinload(UL.unit_load_records).selectinload(ULRecord.location)).paginate(page=page, per_page=per_page, error_out=False)
            return [ul.to_dict() for ul in uls.items]
        else:
            ul = UL.query.options(selectinload(UL.unit_load_records).selectinload(ULRecord.location)).filter_by(id=ulId).first_or_404()
            return ul.to_dict()

    @api_namespace.expect(ul_model)
    @api_namespace.marshal_with(ul_model, code=201)
    @request_wrapper
    def post(self):
        data = request.get_json()
        ul = services.create_ul(data)
        return ul.to_dict(), 201
    
    @api_namespace.expect(api_namespace.parser().add_argument('ulId', type=str, required=True, help='The ID of the UL', location='args'), ul_model)
    @api_namespace.marshal_with(ul_model, code=201)
    @request_wrapper
    def patch(self):
        id = request.args.get('ulId')
        ul = UL.query.get_or_404(id)
        data = request.get_json()
        for key, value in data.items():
            if key in ul.__dict__: 
                setattr(ul, key, value)
        db.session.commit()
        return UL.query.get_or_404(ul.id).to_dict()

    @api_namespace.expect(api_namespace.parser().add_argument('ulId', type=str, required=True, help='The ID of the UL', location='args'))
    def delete(self):
        id = request.args.get('ulId')
        ul = UL.query.get_or_404(id)
        db.session.delete(ul)
        db.session.commit()
        return {"message": "UL deleted successfully"}


@api_namespace.route('/store', methods=['POST'])
class ULsStoreResource(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.post_parser = reqparse.RequestParser()
        self.post_parser.add_argument('ulId', type=str, required=False, help='The ID of the UL', location='args')
        self.post_parser.add_argument('itemId', type=str, required=False, help='The ID of the Item', location='args')
        self.post_parser.add_argument('itemNumber', type=int, required=False, help='The Number of the Item', location='args')

    @request_wrapper
    @api_namespace.doc(params={
        'ulId': {'in': 'query', 'type': 'string', 'description': 'The ID of the UL for which a ULRecord should be created'},
        'itemId': {'in': 'query', 'type': 'string', 'description': 'The ID of the Item for which a UL should be created'},
        'itemNumber': {'in': 'query', 'type': 'integer', 'description': 'The Number of the Item for which a UL should be created'}
    })
    @api_namespace.expect(ul_record_model)
    @api_namespace.marshal_with(ul_record_model, code=201)
    def post(self):
        args = self.post_parser.parse_args()
        ulId = args.get('ulId')
        itemId = args.get('itemId')
        itemNumber = args.get('itemNumber')
        payload_ulId = request.get_json().get('ulId', False)

        data = request.get_json()
        if not ulId and not payload_ulId:
            if itemId: 
                data.update({'itemId': itemId})
            elif itemNumber:
                data.update({'itemNumber': itemNumber})
            ul = services.create_ul(data)
        elif ulId:
            ul = UL.query.get_or_404(ulId) 
        elif payload_ulId: 
            ul = UL.query.get_or_404(payload_ulId)
        else: 
            raise KeyError("UL Record ID, itemId and itemNumber not provided or found")
        ulrec = services.store_ul(ul, data)
        return ulrec.to_dict()

@api_namespace.route('/retrieve', methods=['POST'])
class ULsRetrieveResource(Resource):
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.post_parser = reqparse.RequestParser()
        self.post_parser.add_argument('ulId', type=str, required=False, help='The ID of the UL', location='args')
        self.post_parser.add_argument('finalRetrieval', type=str, required=False, help='Whether this is the final retrieval', location='args')

    @api_namespace.marshal_with(ul_record_model, code=201)
    @api_namespace.expect(ul_record_model)
    @api_namespace.doc(params={
        'ulId': {'in': 'query', 'type': 'string', 'description': 'The ID of the UL for which a ULRecord should be created'},
        'finalRetrieval': {'in': 'query', 'type': 'boolean', 'description': 'Whether this is the final retrieval'}
    })
    @request_wrapper
    def post(self):
        args = self.post_parser.parse_args()
        ulId = args.get('ulId')
        payload_ulId = request.get_json().get('ulId', False)
        final_retrieval = args.get('finalRetrieval')
        if isinstance(final_retrieval, str):
            final_retrieval = final_retrieval.lower() == 'true'
        elif final_retrieval is None:
            final_retrieval = False
        payload_final_retrieval = request.get_json().get('finalRetrieval', False)
        if isinstance(payload_final_retrieval, str):
            payload_final_retrieval = payload_final_retrieval.lower() == 'true'
        elif payload_final_retrieval is None:
            payload_final_retrieval = False

        data = request.get_json()
        if ulId: 
            ul = UL.query.get_or_404(ulId)
        elif payload_ulId:
            ul = UL.query.get_or_404(payload_ulId)
        else:
            raise KeyError("UL Record ID not provided")
        if final_retrieval or payload_final_retrieval:
            ulrec = services.retrieve_ul(ul, data, final_retrieval=True)
        else: 
            ulrec = services.retrieve_ul(ul, data, final_retrieval=False)
        return ulrec.to_dict()

@api_namespace.route('/stored', methods=['GET'])
class StoredULsResource(Resource):
    @api_namespace.expect(ul_model)
    @api_namespace.marshal_with(ul_model, code=201)
    @request_wrapper
    def get(self):
        stored_uls = services.get_stored_uls()
        return [ul.to_dict() for ul in stored_uls]