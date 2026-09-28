from flask import Flask, render_template, Blueprint, request
from sqlalchemy.orm import selectinload
from storage_location_tracking.models import Item, UL, Location, ULRecord, db, batch_compute_quantities
import storage_location_tracking.services as services
import uuid

ui_blueprint = Blueprint('ui', __name__, template_folder='templates', static_folder='static')


@ui_blueprint.route('/')
def index():
    return render_template('base.html')

@ui_blueprint.route('/items')
def items():
    page = request.args.get('page', 1, type=int)
    items = Item.query.paginate(page=page, per_page=20)
    batch_compute_quantities(items.items)
    return render_template('items.html', items=items)

@ui_blueprint.route('/uls')
def uls():
    page = request.args.get('page', 1, type=int)
    uls = UL.query.options(
        selectinload(UL.item),
        selectinload(UL.unit_load_records).selectinload(ULRecord.location)
    ).paginate(page=page, per_page=20)
    
    for ul in uls.items:
        ul.itemNumber = ul.item.number
        
        latest_record = None
        if ul.unit_load_records:
            latest_record = max(ul.unit_load_records, key=lambda r: r.stored_at)

        if ul.is_stored and latest_record:
            ul.locationName = latest_record.location.name
            ul.stored_at = latest_record.stored_at
        else :
            ul.locationName = None
            ul.stored_at = None
    return render_template('uls.html', uls=uls)

@ui_blueprint.route('/ulhistory')
def history():
    page = request.args.get('page', 1, type=int)

    query = ULRecord.query.options(
        selectinload(ULRecord.location),
        selectinload(ULRecord.ul_instance).selectinload(UL.item)
    )

    if 'ulId' in request.args:
        ulId = request.args.get('ulId', type=uuid.UUID)
        query = query.filter_by(ulId=ulId)

    history = query.paginate(page=page, per_page=20)

    for record in history.items:
        record.locationName = record.location.name if record.location else None
        record.itemNumber = record.ul_instance.item.number if record.ul_instance and record.ul_instance.item else None

    return render_template('ulhistory.html', history=history)


@ui_blueprint.route('/locations')
def locations():
    locations = Location.query.all()
    occupied_locations = services.get_occupied_locations()
    for location in locations:
        location.is_occupied = location in occupied_locations
    return render_template('locations.html', locations=locations)