from storage_location_tracking.models import db, UL, Location, Item, ULRecord
import uuid
from datetime import datetime
from sqlalchemy import exists, and_

class InvalidForeignKeyError(Exception):
    """
    Exception raised when an invalid foreign key is provided
    """
    pass

def get_item(data: dict): 
    """
    Get the item from the database based on the provided data.
    Searches for either itemId or itemNumber in the data.

    :param data: The data containing the itemId or itemNumber attribute
    """
    if data.get("itemId", False):
        item = Item.query.filter_by(id=data["itemId"]).first()
    elif data.get("itemNumber", False):
        item = Item.query.filter_by(number=str(data["itemNumber"])).first()
    else:
        raise InvalidForeignKeyError("Invalid itemId or itemNumber")
    return item

def get_location(data: dict):
    """
    Get the location from the database based on the provided data.
    Searches for either locationId or locationName in the data.

    :param data: The data containing the locationId or locationName attribute
    """
    if data.get("locationId", False):
        location = Location.query.filter_by(id=data["locationId"]).first()
    elif data.get("locationName", False):
        location = Location.query.filter_by(name=str(data["locationName"])).first()
    elif data.get("stationName", False):
        location = Location.query.filter_by(name=str(data["stationName"])).first()
    else:
        raise InvalidForeignKeyError("Invalid locationId, locationName or stationName")
    return location

def find_locations(data: dict):
    """
    Find a location in the database based on the provided data.
    Searches for itemId, itemNumber or a ulId in the data.

    :param data: The data containing the itemId, itemNumber or ulId attribute
    """
    if data.get("itemId", False) or data.get("itemNumber", False):
        uls = get_uls_for_item(data)
    elif data.get("ulId", False):
        uls = UL.query.filter_by(id=data["ulId"]).all() 
    else: 
        raise InvalidForeignKeyError("Invalid itemId, itemNumber or ulId")
    
    if not uls:
        raise InvalidForeignKeyError("No ULs found")
        
    ul_ids = [ul.id for ul in uls]
    locations = Location.query.join(ULRecord).filter(ULRecord.ulId.in_(ul_ids)).all()
    # Ensure distinct if required
    return list(set(locations))

def get_uls_for_item(data: dict):
    """
    Get the UL from the database based on the provided data.
    Searches for all ULs for a given itemId or itemNumber in the data that are not 
    completly retrieved yet

    :param data: The data containing the itemId or itemNumber attribute 
    """
    item = get_item(data)
    try: 
        uls = UL.query.filter_by(itemId=item.id, completly_retrieved=False).all()
        return uls
    except AttributeError:
        raise InvalidForeignKeyError("Item not found")

def create_ul(data: dict):
    """
    Create a new UL based on the provided data.

    :param data: The data containing the itemId attribute
    """
    item = get_item(data)
    if item is None: 
        raise InvalidForeignKeyError("Item not found")
    ul = UL(itemId=item.id)
    db.session.add(ul)
    db.session.flush()
    db.session.refresh(ul)
    return ul

def store_ul(ul: UL, data: dict):
    """
    Store a UL in a location based on the provided data.
    Creates a new ULRecord entry in the database.

    :param ul: The UL to store
    :param data: The data containing the stored_at attribute
    """
    if ul.is_stored:
        raise KeyError("UL is already stored")
    if ul.completly_retrieved:
        raise KeyError("UL is already completly retrieved")
    # Check if there exists a ULRecord for this UL that is not retrieved yet
    existing_ul_record = ULRecord.query.filter_by(ulId=ul.id, retrieved_at=None).first()
    if existing_ul_record:
        raise KeyError("There is already a ULRecord for this UL that is not retrieved yet")
    stored_at = data.get("stored_at", datetime.now())
    location = get_location(data) 
    
    if location.type not in ['sink', 'source']:
        is_occupied = db.session.query(
            exists().where(
                and_(
                    ULRecord.locationId == location.id,
                    ULRecord.retrieved_at.is_(None)
                )
            )
        ).scalar()
        if is_occupied:
            raise KeyError("Location is already occupied")

    ulRecord = ULRecord(ulId=ul.id, locationId=location.id, stored_at=stored_at)
    db.session.add(ulRecord)    
    db.session.commit()
    db.session.refresh(ulRecord)
    return ulRecord

def retrieve_ul(ul: UL, data: dict, final_retrieval: bool = False):
    """
    Retrieve a UL from a location based on the provided data.
    Updates the stored_at attribute of the ULRecord entry in the database.
    
    :param ul: The UL to retrieve
    :param data: The data containing the retrieved_at attribute
    """
    retrieved_at = data.get("retrieved_at", datetime.now())
    if retrieved_at is None: 
        retrieved_at = datetime.now()
    ulRecord = ULRecord.query.filter_by(ulId=ul.id, retrieved_at=None).order_by(ULRecord.stored_at.desc()).first()
    ulRecord.retrieved_at = retrieved_at
    if final_retrieval:
        ul.completly_retrieved = True
    db.session.commit()
    return ulRecord

def get_stored_uls():
    """
    Get all stored ULs from the database.
    """
    from sqlalchemy.orm import selectinload
    from storage_location_tracking.models import ULRecord
    return UL.query.options(selectinload(UL.unit_load_records).selectinload(ULRecord.location)).filter(UL.is_stored == True).all()

def get_latest_ul_record(ulId: uuid.UUID):
    """
    Get the latest ULRecord entry for a UL from the database.
    
    :param ulId: The UUID of the UL
    """
    return ULRecord.query.filter_by(ulId=ulId).order_by(ULRecord.stored_at.desc()).first()

def get_occupied_locations(include_amrs=True): 
    """
    Get all occupied locations from the database.
    """
    query = Location.query.join(ULRecord).filter(
        ULRecord.retrieved_at.is_(None),
        Location.type.notin_(['sink', 'source'])
    )
    if not include_amrs:
        query = query.filter(Location.type == 'station')
    return query.distinct().all()

def get_empty_locations(include_amrs=True):
    """
    Get all empty locations from the database.
    """
    active_records_subquery = db.session.query(ULRecord.locationId).filter(
        ULRecord.retrieved_at.is_(None)
    ).subquery()
    
    query = Location.query.outerjoin(
        active_records_subquery, Location.id == active_records_subquery.c.locationId
    ).filter(
        active_records_subquery.c.locationId.is_(None),
        Location.type.notin_(['sink', 'source'])
    )
    
    if not include_amrs:
        query = query.filter(Location.type == 'station')
    return query.all()

def get_history(ulId: uuid.UUID):
    """
    Get the history of a UL from the database.
    
    :param ulId: The UUID of the UL
    """
    return ULRecord.query.filter_by(ulId=ulId).all()