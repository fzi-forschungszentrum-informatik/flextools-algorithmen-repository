from flask import Blueprint
from flask_restx import Api

from .locations import api_namespace as locations_namespace
from .items import api_namespace as items_namespace
from .ulRecords import api_namespace as ulRecords_namespace
from .uls import api_namespace as uls_namespace
from .inventory import api_namespace as inventory_namespace

api_blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(
    api_blueprint, 
    version='1.0', 
    title='Storage Location Tracking API', 
    description='A simple API for tracking items and locations'
)

api.add_namespace(locations_namespace)
api.add_namespace(items_namespace)
api.add_namespace(ulRecords_namespace)
api.add_namespace(uls_namespace)
api.add_namespace(inventory_namespace)