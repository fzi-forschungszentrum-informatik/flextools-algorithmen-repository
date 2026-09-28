import json
import time
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, literal
from storage_location_tracking.models import db, Item, UL, Location, ULRecord, InventoryHistory
import storage_location_tracking.services as services
from datetime import datetime  

class LayoutHandler:
    """
    Class to handle loading the layout from a JSON file and updating the database with the new layout.
    """

    @staticmethod
    def load_layout(app, layout_file):
        """
        Load the layout from a JSON file and update the database with the new layout.

        :param app: The Flask app.
        :param layout_file: The path to the JSON file containing the layout. 
        """
        try:
            with open(layout_file) as f:
                layout = json.load(f)
                LayoutHandler.create_locations(app, layout)
        except Exception as e:
            print(f"error loading layout: {e}")
            layout = {}
        return layout

    @staticmethod
    def load_items(app, items_file):
        """
        Load the items from a JSON file and update the database with the new items.

        :param app: The Flask app.
        :param items_file: The path to the JSON file containing the items. 
        """
        try:
            with open(items_file) as f:
                items = json.load(f)
                LayoutHandler.create_items(app, items)
        except Exception as e:
            print(f"error loading items: {e}")
            items = {}
        return items

    @staticmethod
    def load_records(app, records_file): 
        """
        Load the records from a JSON file and update the database with the new records.
        
        :param app: The Flask app.
        :param records_file: The path to the JSON file containing the records.
        """
        try: 
            with open(records_file) as f: 
                records = json.load(f)
                LayoutHandler.create_records(app, records)
        # except Exception as e:
        except KeyError as e:
            print(f"error loading records: {e}")
            records = {}
        return records

    @staticmethod
    def create_locations(app, layout):
        """
        Create the locations in the database based on the layout.

        :param app: The Flask app.
        :param layout: The layout JSON object.
        """
        with app.app_context():
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    with db.session.begin():
                        db.session.query(Location).delete()
                        db.session.commit()
                    with db.session.begin():
                        new_locations = [
                            Location(
                                id=location.get("stationId", None),
                                name=location.get("stationName", None),
                                description=location.get("stationDescription", None),
                                x=location["stationPosition"]["x"],
                                y=location["stationPosition"]["y"],
                                type=location.get("type", "station"),
                                interactionNodeIds = location["interactionNodeIds"]
                            )
                            for location in layout["layouts"][0].get("stations", [])
                        ]
                        db.session.bulk_save_objects(new_locations)
                        db.session.commit()
                        break
                except SQLAlchemyError as e:
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed to update locations after {max_retries} attempts: {str(e)}")
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
        if db.session.query(Location).count() != len(layout["layouts"][0].get("stations", [])):
            raise Exception("Failed to update locations: count mismatch") 
 


    @staticmethod
    def create_items(app, items):
        """
        Creates items from a file.

        :param items: The contents of the file.
        :type items: str
        """
        with app.app_context():
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    with db.session.begin():
                        db.session.query(InventoryHistory).delete()
                        db.session.query(Item).delete()
                        db.session.commit()
                    with db.session.begin():
                        new_items = [
                            Item(
                                number=item['number'],
                                description=item['description'],
                                weight=item.get('weight'),  # Use .get() to handle missing columns
                                height=item.get('height'),
                                width=item.get('width'),
                                length=item.get('length')
                            )
                            for item in items.get("items", [])
                        ]
                        db.session.bulk_save_objects(new_items)
                        db.session.commit()
                
                    break
                except SQLAlchemyError as e:
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed to update items after {max_retries} attempts: {str(e)}")
                    time.sleep(0.5 * (attempt + 1))

    @staticmethod
    def create_records(app, records):
        """
        Create records from a file, handling 'completly_retrieved' status.
        """
        import uuid
        with app.app_context():
            try:
                # Temporarily disable event listeners to avoid N+1 count updates
                import storage_location_tracking.models as models
                models.DISABLE_EVENTS = True

                db.session.query(ULRecord).delete()
                db.session.query(UL).delete()
                db.session.commit()

                item_map = {item.number: item.id for item in db.session.query(Item).all()}
                location_map = {loc.name: loc.id for loc in db.session.query(Location).all()}

                ul_mappings = []
                ul_record_mappings = []

                for data in records.get("records", []):
                    item_number = str(data['itemNumber'])
                    item_id = item_map.get(item_number)
                    if item_id is None:
                        raise services.InvalidForeignKeyError(f"Item not found for itemNumber: {item_number}")

                    stored_at = data.get('stored_at', datetime.now())
                    retrieved_at = data.get('retrieved_at', None)
                    completly_retrieved = data.get('completly_retrieved', False)
                    
                    ul_id = uuid.uuid4()
                    completly_retrieved_val = True if (completly_retrieved and retrieved_at is not None) else False
                    
                    ul_mappings.append({
                        'id': ul_id,
                        'itemId': item_id,
                        'completly_retrieved': completly_retrieved_val
                    })

                    location_name = str(data['locationName'])
                    location_id = location_map.get(location_name)
                    if location_id is None:
                        raise services.InvalidForeignKeyError(f"Location not found for locationName: {location_name}")

                    ul_record_mappings.append({
                        'id': uuid.uuid4(),
                        'ulId': ul_id,
                        'locationId': location_id,
                        'stored_at': stored_at,
                        'retrieved_at': retrieved_at
                    })

                if ul_mappings:
                    db.session.bulk_insert_mappings(UL, ul_mappings)
                if ul_record_mappings:
                    db.session.bulk_insert_mappings(ULRecord, ul_record_mappings)
                db.session.commit()

                # 1. Events wieder aktivieren für den normalen API-Betrieb
                models.DISABLE_EVENTS = False

                # 2. InventoryHistory aktualisieren
                LayoutHandler.generate_initial_inventory_history()

            except SQLAlchemyError as e:
                raise Exception(f"Failed to update records: {str(e)}")
            finally:
                models.DISABLE_EVENTS = False

    @staticmethod
    def generate_initial_inventory_history():
        """
        Calculates the current active inventory for all items and creates the initial InventoryHistory records.
        """
        from sqlalchemy import func
        # Clear existing inventory history
        db.session.query(InventoryHistory).delete()
        db.session.commit()

        # Calculate current inventory levels for active ULs
        active_uls = db.session.query(
            UL.itemId, 
            func.count(UL.id).label('qty')
        ).filter(
            UL.completly_retrieved == False
        ).group_by(UL.itemId).all()

        history_records = []
        now = datetime.now()
        
        for item_id, qty in active_uls:
            import uuid
            history_records.append({
                "id": uuid.uuid4(),
                "item_id": item_id,
                "quantity": qty,
                "timestamp": now
            })

        if history_records:
            db.session.bulk_insert_mappings(InventoryHistory, history_records)
            db.session.commit()
