from flask import request
from flask_restx import Namespace, Resource, fields, reqparse
from storage_location_tracking.models import db, Location
import storage_location_tracking.services as services
from .api import request_wrapper


api_namespace = Namespace('locations')

station_position_model = api_namespace.model('stationPostion', {
    'x': fields.Float(description='The x coordinate of the location'),
    'y': fields.Float(description='The y coordinate of the location'),
    'theta': fields.Float(description='The angle of the location')
})
location_model = api_namespace.model('Location', {
    'stationId': fields.String(description='The unique identifier of the location'),
    'stationName': fields.String(description='The unique name of the location'),
    'stationDescription': fields.String(description='The description of the location'),
    'interactionNodeIds': fields.List(fields.String(description='The IDs of the interaction nodes')),
    'stationPosition': fields.Nested(station_position_model),
    'type': fields.String(description='The type of the location (station, source, sink or vehicle)')
})

@api_namespace.route('/', methods=['GET', 'POST', 'PATCH', 'DELETE'])
class LocationsResource(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_parser = reqparse.RequestParser()
        self.get_parser.add_argument('stationId', type=str, required=False, help='The stationId of the location', location='args')
        self.get_parser.add_argument('stationName', type=str, required=False, help='The stationName of the location', location='args')
        self.get_parser.add_argument('itemId', type=str, required=False, help='The ID of the Item', location='args')
        self.get_parser.add_argument('itemNumber', type=int, required=False, help='The Number of the Item', location='args')
        self.get_parser.add_argument('type', type=str, required=False, help='The type of the location', location='args')
        self.get_parser.add_argument('ulId', type=str, required=False, help='The ID of the ul', location='args')
        self.get_parser.add_argument('page', type=int, default=1, help='Page number', location='args')
        self.get_parser.add_argument('per_page', type=int, default=20, help='Items per page', location='args')

    @api_namespace.marshal_with(location_model, as_list=True)
    @api_namespace.doc(params={
        'stationId': {'in': 'query', 'type': 'string', 'description': 'The stationId of the location'},
        'stationName': {'in': 'query', 'type': 'string', 'description': 'The name of the location'}, 
        'itemId': {'in': 'query', 'type': 'string', 'description': 'The ID of the Item'},
        'itemNumber': {'in': 'query', 'type': 'integer', 'description': 'The Number of the Item'},
        'type': {'in': 'query', 'type': 'string', 'description': 'The type of the location'},
        'ulId': {'in': 'query', 'type': 'string', 'description': 'The ID of the ul'},
        'page': {'in': 'query', 'type': 'integer', 'description': 'Page number'},
        'per_page': {'in': 'query', 'type': 'integer', 'description': 'Items per page'}
    })
    @request_wrapper
    def get(self):
        args = self.get_parser.parse_args()
        stationId = args.get('stationId')
        stationName = args.get('stationName')
        itemId = args.get('itemId')
        itemNumber = args.get('itemNumber')
        loctype = args.get('type')
        ulId = args.get('ulId')
        page = args['page']
        per_page = args['per_page']

        if stationId:   
            id = stationId
            location = Location.query.get_or_404(id)  
            return location.to_dict()
        elif stationName:
            location = services.get_location({'stationName': stationName}) 
            return location.to_dict()
        elif itemId or itemNumber or ulId:
            locations = services.find_locations(args)
            return [location.to_dict() for location in locations]
        elif loctype:
            locations = Location.query.filter_by(type=loctype).paginate(page=page, per_page=per_page, error_out=False)
            return [location.to_dict() for location in locations.items]
        else:
            locations = Location.query.paginate(page=page, per_page=per_page, error_out=False)
            return [location.to_dict() for location in locations.items]
         
    @api_namespace.expect(location_model)
    @api_namespace.marshal_with(location_model)
    @request_wrapper
    def post(self):
        data = request.get_json()
        for coord in ['x', 'y']:
            if coord in data and data[coord] == '':
                data[coord] = None
        if 'stationPosition' not in data:
            data['stationPosition'] = {}
        new_location = Location(
            id=data.get('stationId', None),
            name=data.get('stationName', None),
            description=data.get('stationDescription', None),
            interactionNodeIds=data.get('interactionNodeIds', None),
            x=data['stationPosition'].get('x', None),
            y=data['stationPosition'].get('y', None),
            theta=data['stationPosition'].get('theta', None),
            type=data.get('type', None)
        )
        db.session.add(new_location)
        db.session.commit()
        return Location.query.get_or_404(new_location.id).to_dict()  

    @api_namespace.doc(params={
        'stationId': {'in': 'query', 'type': 'string', 'description': 'The stationId of the location'},
        'stationName': {'in': 'query', 'type': 'integer', 'description': 'The name of the location'}
    })
    @api_namespace.expect(location_model)
    @api_namespace.marshal_with(location_model)
    @request_wrapper
    def patch(self):
        args = self.get_parser.parse_args()
        stationId = args.get('stationId')
        stationName = args.get('stationName')
        payload_stationId = request.get_json().get('stationId', False)
        payload_stationName = request.get_json().get('stationName', False)

        if stationId:
            location = Location.query.get_or_404(stationId) 
        elif payload_stationId:
            location = Location.query.get_or_404(payload_stationId)
        elif stationName:
            location = services.get_location({'stationName': stationName})
        elif payload_stationName:
            location = services.get_location({'stationName': payload_stationName})
        else: 
            return {"error": "No locationId or locationName provided"}, 400
        data = request.get_json()
        location.description = data.get('stationDescription', location.description)
        location.interactionNodeIds = data.get('interactionNodeIds', location.interactionNodeIds)
        location.x = data['stationPosition'].get('x', location.x)
        location.y = data['stationPosition'].get('y', location.y)
        location.type = data.get('type', location.type)
        db.session.commit()
        return Location.query.get_or_404(location.id).to_dict()

    @api_namespace.expect(
        api_namespace.parser().add_argument('id', type=str, required=False, help='The ID of the Item', location='args'), 
        api_namespace.parser().add_argument('number', type=int, required=False, help='The Number of the Item', location='args'))
    @api_namespace.marshal_with(location_model)
    def delete(self):
        if request.args.get('id'):
            id = request.args.get('id')  
            location = Location.query.get_or_404(id) 
        elif request.args.get('number'):
            number = request.args.get('number')  
            location = Location.query.filter_by(number=number).first()
        else: 
            return {"error": "No locationId or locationName provided"}, 400
        db.session.delete(location)
        db.session.commit()
        return {"message": "Location deleted successfully"}

@api_namespace.route('/empty', methods=['GET'])
class EmptyLocationsResource(Resource):
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.get_parser = reqparse.RequestParser()
        self.get_parser.add_argument('include_amrs', type=str, required=False, help='Include AMRs in the response', location='args')

    @api_namespace.marshal_with(location_model, as_list=True)
    @api_namespace.doc(params={
        'include_amrs': {'in': 'query', 'type': 'boolean', 'description': 'Include AMRs in the response'}
    })
    @request_wrapper
    def get(self):
        args = self.get_parser.parse_args()
        include_amrs = args.get('include_amrs')
        if isinstance(include_amrs, str):
            include_amrs = include_amrs.lower() == 'true'
        empty_locations = services.get_empty_locations(include_amrs=include_amrs)
        return [location.to_dict() for location in empty_locations]


@api_namespace.route('/occupied', methods=['GET'])
class OccupiedLocationsResource(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_parser = reqparse.RequestParser()
        self.get_parser.add_argument('include_amrs', type=str, required=False, help='Include AMRs in the response', location='args')

    @api_namespace.marshal_with(location_model, as_list=True)
    @api_namespace.doc(params={
        'include_amrs': {'in': 'query', 'type': 'boolean', 'description': 'Include AMRs in the response'}
    })
    @request_wrapper
    def get(self):
        args = self.get_parser.parse_args()
        include_amrs = args.get('include_amrs')
        if isinstance(include_amrs, str):
            include_amrs = include_amrs.lower() == 'true'
        occupied_locations = services.get_occupied_locations(include_amrs=include_amrs)
        return [location.to_dict() for location in occupied_locations]