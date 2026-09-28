from flask import request, jsonify
from flask_restx import Namespace, Resource, fields, reqparse
from storage_location_tracking.models import db, ULRecord
from .api import request_wrapper


api_namespace = Namespace('ulRecords')

ul_record_model = api_namespace.model('ULRecord', {
    'id': fields.String(description='The unique identifier of the ULRecord', readonly=True),
    'locationId': fields.String(description='The ID of the location where the ULRecord is stored'),
    'ulId': fields.String(description='The ID of the UL associated with the ULRecord'),
    'stored_at': fields.String(description='The timestamp when the ULRecord was stored'),
    'retrieved_at': fields.String(description='The timestamp when the ULRecord was retrieved')
})
parser = reqparse.RequestParser()
parser.add_argument('id', type=str, required=False, help='UL Record ID', location='args')
parser.add_argument('page', type=int, default=1, help='Page number', location='args')
parser.add_argument('per_page', type=int, default=20, help='Items per page', location='args')
parser.add_argument('locationId', type=str, required=False, help='Filter by location ID', location='args')
parser.add_argument('ulId', type=str, required=False, help='Filter by UL ID', location='args')
parser.add_argument('start_date', type=str, help='Filter by start date (YYYY-MM-DD)', location='args')
parser.add_argument('end_date', type=str, help='Filter by end date (YYYY-MM-DD)', location='args')


@api_namespace.route('/', methods=['GET', 'PATCH', 'DELETE'])
class ULRecordsResource(Resource):
    @api_namespace.expect(parser)  # Use the parser directly
    @api_namespace.marshal_list_with(ul_record_model)
    @request_wrapper
    def get(self):
        args = parser.parse_args()
        page = args['page']
        per_page = args['per_page']

        query = ULRecord.query
        if args['locationId']:
            query = query.filter_by(locationId=args['locationId'])
        if args['ulId']:
            query = query.filter_by(ulId=args['ulId'])
        if args['start_date']:
            query = query.filter(ULRecord.stored_at >= args['start_date'])
        if args['end_date']:
            query = query.filter(ULRecord.stored_at <= args['end_date'])

        ul_records = query.paginate(page=page, per_page=per_page, error_out=False)
        return [ul_record.to_dict() for ul_record in ul_records.items]

    @api_namespace.expect(api_namespace.parser().add_argument('id', type=str, required=True, help='The ID of the UL Record', location='args'),
                          ul_record_model)
    @api_namespace.marshal_with(ul_record_model, code=201)
    @request_wrapper
    def patch(self):
        ulId = request.args.get('id')
        ul_record = ULRecord.query.get_or_404(ulId)
        data = request.get_json()
        for key, value in data.items():
            if key in ul_record.__dict__: 
                setattr(ul_record, key, value)
        db.session.commit()
        return ULRecord.query.get_or_404(ul_record.id).to_dict()
    
    @api_namespace.expect(api_namespace.parser().add_argument('id', type=str, required=True, help='The ID of the UL Record', location='args'))
    def delete(self):
        ulId = request.args.get('id')
        ul_record = ULRecord.query.get_or_404(ulId)
        db.session.delete(ul_record)
        db.session.commit()
        return {"message": "UL Record deleted successfully"}