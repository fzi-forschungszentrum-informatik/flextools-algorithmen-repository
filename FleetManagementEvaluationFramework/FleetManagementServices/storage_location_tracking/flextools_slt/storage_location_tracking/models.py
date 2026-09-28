from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, ARRAY, TEXT
from sqlalchemy.orm import validates
from sqlalchemy import text, event, CheckConstraint, select, Index
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
import uuid
import datetime

db = SQLAlchemy()

# Global flag to disable event listeners during large bulk imports
DISABLE_EVENTS = False

class ULRecord(db.Model):
    """
    A unit load record represents the movement of a real object within a storage location.
    Each time the real object is moved, a new ULRecord object is created with the location, storage, and retrieval timestamps.

    :param id: The unique identifier of the ULRecord.
    :type id: UUID
    :param locationId: The ID of the location where the ULRecord is stored.
    :type locationId: UUID
    :param ulId: The ID of the UL associated with the ULRecord.
    :type ulId: UUID
    :param stored_at: The timestamp when the ULRecord was stored.
    :type stored_at: datetime
    :param retrieved_at: The timestamp when the ULRecord was retrieved.
    :type retrieved_at: datetime
    :ivar location: The location object associated with the ULRecord.
    :vartype location: Location
    :ivar ul_instance: The UL object associated with the ULRecord.
    :vartype ul_instance: UL
    :raises ValueError: If an attempt is made to change the ID or location ID of an existing ULRecord.
    :return: None
    :rtype: None
    """
    __tablename__ = 'ul_record'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    # locationId = db.Column(UUID(as_uuid=True), db.ForeignKey('location.id', ondelete='CASCADE'), nullable=True)
    locationId = db.Column(db.String(50), db.ForeignKey('location.id', ondelete='CASCADE'), nullable=True)
    ulId = db.Column(UUID(as_uuid=True), db.ForeignKey('ul.id'), nullable=False)
    stored_at = db.Column(db.DateTime(timezone=False), nullable=False, default=func.now())
    retrieved_at = db.Column(db.DateTime(timezone=False), nullable=True)

    location = db.relationship('Location', backref=db.backref('ul_records', lazy=True, cascade='all'))    
    ul_instance = db.relationship('UL', back_populates='unit_load_records', lazy=True)
    __table_args__ = (
        Index('location_idx', 'locationId'),
        Index('ul_idx', 'ulId'),
        Index('stored_at_idx', 'stored_at'),
        Index('retrieved_at_idx', 'retrieved_at'),  # Add index for retrieved_at
    )

    def __repr__(self):
        return f"ULRecord(id={self.id}, locationId={self.locationId}, ulId={self.ulId}, stored_at={self.stored_at}, retrieved_at={self.retrieved_at})"
    
    def to_dict(self):
        """
        Returns a dictionary representation of the ULRecord object.
        """
        return {
            "id": str(self.id),
            "locationId": str(self.locationId),
            "ulId": str(self.ulId),
            "stored_at": str(self.stored_at),
            "retrieved_at": str(self.retrieved_at)
        }

    @validates('id')
    def validate_id(self, key, value):
        """
        Validates the ID of the ULRecord object."""
        if self.id and self.id != value:
            raise ValueError("Cannot change the ID of an ULRecord")
        return value
    
    @validates('locationId')
    def validate_locationId(self, key, value):
        """Validates the location ID of the ULRecord object."""
        if self.locationId and self.locationId != value:
            raise ValueError("Cannot change the location ID of an ULRecord")
        return value


class Location(db.Model):
    """
    A location represents a physical storage location in a warehouse.

    :param id: The unique identifier of the location.
    :type id: UUID
    :param name: The unique name of the location.
    :type name: str
    :param description: The description of the location.
    :type description: str
    :param interactionNodeIds: The ID of the map associated with the location.
    :type interactionNodeIds: UUID
    :param x: The x coordinate of the location.
    :type x: float
    :param y: The y coordinate of the location.
    :type y: float
    :param type: The type of the location (station or vehicle).
    :type type: str
    :ivar ul_records: The ULRecord objects associated with the location.
    :vartype ul_records: List[ULRecord]
    :raises ValueError: If an attempt is made to change the ID, location name, x, y, or type of an existing location.
    """
    __tablename__ = 'location'
    # id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    id = db.Column(db.String(50), unique=True, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    interactionNodeIds = db.Column(ARRAY(db.String), nullable=True)
    height = db.Column(db.Float, nullable=False, default=0)
    x = db.Column(db.Float, nullable=True, default=None)
    y = db.Column(db.Float, nullable=True, default=None)
    theta = db.Column(db.Float, nullable=False, default=0)
    type = db.Column(db.String(50), nullable=False, default="station")
    is_source = db.Column(db.Boolean, default=False, nullable=False)
    is_sink = db.Column(db.Boolean, default=False, nullable=False)
    __table_args__ = (
        CheckConstraint("type IN ('station', 'vehicle', 'source', 'sink')", name='location_type_check'),
        Index('name_idx', 'name'),  # Add index for name
        Index('type_idx', 'type'),  # Add index for type
    )

    def __repr__(self):
        return f"Location(id={self.id}, name={self.name})"
    
    def to_dict(self):
        """
        Returns a dictionary representation of the Location object."""
        return {
            "stationId": str(self.id),
            "stationName": self.name,
            "stationDescription": self.description,
            "interactionNodeIds": self.interactionNodeIds,
            "stationPosition": {
                "x": self.x,
                "y": self.y, 
                "theta": self.theta
                },
            "type": self.type
        }

    @validates('id')
    def validate_id(self, key, value):
        """
        Validates the ID of the Location object."""
        if self.id and self.id != value:
            raise ValueError("Cannot change the ID of a location")
        return value
    
    @validates('name')
    def validate_name(self, key, value):
        """
        Validates the location name of the Location object."""
        if self.name and self.name != value:
            raise ValueError("Cannot change the location name of a location")
        return value

    @validates('x')
    def validate_location_x(self, key, value):
        """
        Validates the x coordinate of the Location object."""
        if self.x and self.x != value:
            raise ValueError("Cannot change the x coordinate of a location")
        return value
    
    @validates('y')
    def validate_location_y(self, key, value):
        """
        Validates the y coordinate of the Location object."""
        if self.y and self.y != value:
            raise ValueError("Cannot change the y coordinate of a location")
        return value
    
    @validates('type')
    def validate_location_type(self, key, value):
        """
        Validates the type of the Location object."""
        if self.type and self.type != value:
            raise ValueError("Cannot change the type of a location")
        return value


class UL(db.Model):
    """
    A unit load represents a real object that can be stored in a warehouse.

    :param id: The unique identifier of the UL.
    :type id: UUID
    :param itemId: The ID of the item associated with the UL.
    :type itemId: UUID
    :param completly_retrieved: A boolean indicating if the UL has been completely retrieved.
    :type completly_retrieved: bool
    :param has_been_stored: A boolean indicating if the UL has been stored.
    :type has_been_stored: bool
    :ivar item: The item object associated with the UL.
    :vartype item: Item
    :ivar unit_load_records: The ULRecord objects associated with the UL.
    :vartype unit_load_records: List[ULRecord]
    :raises ValueError: If an attempt is made to change the ID or item ID of an existing UL.
    """
    __tablename__ = 'ul'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    itemId = db.Column(UUID(as_uuid=True), db.ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    completly_retrieved = db.Column(db.Boolean, default=False, nullable=False)

    item = db.relationship('Item', back_populates='uls')
    unit_load_records = db.relationship('ULRecord', back_populates='ul_instance', lazy=True)
    __table_args__ = (
        Index('item_id_idx', 'itemId'),  # Add index for itemId
        Index('completly_retrieved_idx', 'completly_retrieved'),  # Add index for completly_retrieved
    )

    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self._original_id = self.id

    def __repr__(self):
        return f"UL(id={self.id}, itemId={self.itemId}, is_stored={self.is_stored})"

    def to_dict(self):
        """
        Returns a dictionary representation of the UL object.
        """
        return {
            "ulId": str(self.id),
            "itemId": str(self.itemId),
            "is_stored": self.is_stored, 
            "completly_retrieved": self.completly_retrieved,
            "has_been_stored": self.has_been_stored
        }

    @validates('id')
    def validate_id(self, key, value):
        """
        Validates the ID of the UL object."""
        if self.id and self.id != value:
            raise ValueError("Cannot change the ID of an UL")
        return value

    @hybrid_property
    def is_stored(self):
        """
        Returns True if the UL is currently stored, False otherwise.
        """
        if len(list(filter(lambda r: r.retrieved_at is None, self.unit_load_records))) > 0: 
            # Use `location` relationship to prevent additional queries in a loop.
            last_record = sorted(self.unit_load_records, key=lambda r: r.stored_at)[-1]
            if last_record.location and last_record.location.type in ["sink", "source"]:
                return False
            return True
        return False

    @is_stored.expression
    def is_stored(cls):
        """
        Returns a SQL expression that checks if the UL is currently stored.
        """
        return cls.unit_load_records.any(ULRecord.retrieved_at == None)

    @hybrid_property
    def has_been_stored(self):
        """
        Returns True if the UL has been stored at least once, False otherwise.
        """
        return len(self.unit_load_records) > 0
    
    @has_been_stored.expression
    def has_been_stored(cls):
        """
        Returns a SQL expression that checks if the UL has been stored at least once.
        """
        return cls.unit_load_records.any()


class Item(db.Model):
    """
    An item represents a type of real object that can be stored in a warehouse.

    :param id: The unique identifier of the item.
    :type id: UUID
    :param number: The unique number of the item.
    :type number: str
    :param description: The description of the item.
    :type description: str
    :ivar uls: The UL objects associated with the item.
    :vartype uls: List[UL]
    :raises ValueError: If an attempt is made to change the ID, item number, or quantity of an existing item.
    """
    __tablename__ = 'item'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    number = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.String(255), default="")
    weight = db.Column(db.Float, nullable=True)
    height = db.Column(db.Float, nullable=True)
    width = db.Column(db.Float, nullable=True)
    length = db.Column(db.Float, nullable=True)

    uls = db.relationship('UL', back_populates='item', cascade='all, delete-orphan')
    __table_args__ = (
        Index('number_idx', 'number'),  # Add index for number
    )

    def __repr__(self):
        return f"Item(id={self.id}, number={self.number}, quantity={self.quantity})"

    def to_dict(self):
        """
        Returns a dictionary representation of the Item object."""
        return {
            "id": str(self.id),
            "number": self.number,
            "quantity": self.quantity,
            "description": self.description
        }
    
    @validates('id')
    def validate_id(self, key, value):
        """
        Validates the ID of the Item object."""
        if self.id and self.id != value:
            raise ValueError("Cannot change the ID of an item")
        return value

    @validates('number')
    def validate_number(self, key, value):
        """
        Validates the number of the Item object."""
        if self.id and self.number != value:
                raise ValueError("Cannot change the item number of an item")
        return value

    @validates('quantity')
    def validate_quantity(self, key, value):
        """
        Validates the quantity of the Item object."""
        if self.id and value != len(self.uls): 
            raise ValueError("Cannot change the quantity of an item manually")
        return value

    @hybrid_property
    def quantity(self):
        """
        Calculates the quantity based on the number of stored ULs associated with this Item.
        Uses a pre-computed cached value when available (set by batch_compute_quantities).
        """
        if hasattr(self, '_cached_quantity'):
            return self._cached_quantity

        from sqlalchemy.orm import object_session
        session = object_session(self)
        if not session:
            return 0
        return session.query(func.count(UL.id))\
            .join(ULRecord, ULRecord.ulId == UL.id)\
            .outerjoin(Location, Location.id == ULRecord.locationId)\
            .filter(UL.itemId == self.id, ULRecord.retrieved_at == None, Location.type.notin_(['sink', 'source']))\
            .scalar() or 0

    @quantity.setter
    def quantity(self, value):
        """
        Raises an error if an attempt is made to set the quantity of an item manually.
        """
        raise ValueError("Cannot set the quantity of an item manually")    


def batch_compute_quantities(items):
    """
    Computes quantities for a list of Item objects in a single GROUP BY SQL query
    and caches the result on each item as _cached_quantity, avoiding N+1 queries.
    """
    if not items:
        return
    from sqlalchemy.orm import object_session
    session = object_session(items[0])
    if not session:
        return
    item_ids = [item.id for item in items]
    qty_rows = (
        session.query(UL.itemId, func.count(UL.id))
        .join(ULRecord, ULRecord.ulId == UL.id)
        .outerjoin(Location, Location.id == ULRecord.locationId)
        .filter(
            UL.itemId.in_(item_ids),
            ULRecord.retrieved_at == None,
            Location.type.notin_(['sink', 'source'])
        )
        .group_by(UL.itemId)
        .all()
    )
    qty_map = {item_id: qty for item_id, qty in qty_rows}
    for item in items:
        item._cached_quantity = qty_map.get(item.id, 0)


class InventoryHistory(db.Model):
    """
    A record of the inventory history for a specific item.

    :param id: The unique identifier of the inventory history record.
    :type id: int
    :param item_id: The ID of the item associated with this inventory history record.
    :type item_id: UUID
    :param quantity: The quantity of the item at the given timestamp.
    :type quantity: int
    :param timestamp: The timestamp when the quantity was recorded.
    :type timestamp: datetime
    :ivar item: The item object associated with this inventory history record.
    :vartype item: Item
    """
    __tablename__ = 'inventory_history'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    item_id = db.Column(UUID(as_uuid=True), db.ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)

    item = db.relationship('Item', backref='inventory_history')
    __table_args__ = (
        Index('inventory_item_id_idx', 'item_id'),  # Add index for item_id
        Index('timestamp_idx', 'timestamp'),  # Add index for timestamp
    )

    def __repr__(self):
        return f"InventoryHistory(item_id={self.item_id}, quantity={self.quantity}, timestamp={self.timestamp})"

    def to_dict(self):
        """
        Returns a dictionary representation of the InventoryHistory object.
        """
        return {
            "id": str(self.id),
            "item_id": str(self.item_id),
            "item_number": self.item.number,
            "quantity": self.quantity,
            "timestamp": self.timestamp.isoformat()  # Format timestamp in ISO 8601
        }

    @staticmethod
    def query_inventory_history(id=False, item_id=False, item_number=False, timestamp=False):
        """
        Queries the InventoryHistory table based on the provided parameters.

        :param id: The unique identifier of the inventory history record.
        :type id: UUID
        :param item_id: The ID of the item associated with the inventory history record.
        :type item_id: UUID
        :param timestamp: The timestamp to filter the inventory history records.
        :type timestamp: datetime
        :return: A list of InventoryHistory records matching the query.
        :rtype: List[InventoryHistory]
        """
        query = db.session.query(InventoryHistory)
        if item_number and not item_id:
            item_id = Item.query.filter_by(number=item_number).first().id

        if id:
            return query.filter_by(id=id).first()
        
        if item_id and timestamp:
            return query.filter(
                InventoryHistory.item_id == item_id,
                InventoryHistory.timestamp <= timestamp
            ).order_by(InventoryHistory.timestamp.desc()).first()
        
        if item_id:
            return query.filter_by(item_id=item_id).all()
        
        if timestamp:
            return query.filter(InventoryHistory.timestamp <= timestamp).order_by(InventoryHistory.timestamp.desc()).all()
        
        return query.all()
    
@event.listens_for(UL, 'after_insert')
@event.listens_for(UL, 'after_update')
@event.listens_for(UL, 'after_delete')
def update_item_quantity(mapper, connection, target):
    """
    Event listener to update the inventory history whenever a UL is created, updated, or deleted.
    """
    global DISABLE_EVENTS
    if DISABLE_EVENTS:
        return

    if target.item is None: 
        target = db.session.query(UL).get(target.id)
    
    if target.item is not None: 
        item = target.item
        quantity = db.session.execute(select(func.count(UL.id)).where(
            UL.itemId == item.id,
            UL.completly_retrieved == False
        )).scalar()
        old_inventory_history = InventoryHistory.query_inventory_history(item_id=item.id, timestamp=datetime.datetime.now())
        if old_inventory_history is not None and old_inventory_history.quantity == quantity:
            return
        connection.execute(
            InventoryHistory.__table__.insert(),
            {
                "item_id": item.id,
                "quantity": quantity,
                "timestamp": datetime.datetime.now()
            }
        )