import time
import json
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from storage_location_tracking import create_app 
from storage_location_tracking.models import db
from storage_location_tracking.layout_handler import LayoutHandler

app = create_app()

def check_database_health(engine, max_retries=5, retry_delay=1):
    """Checks if the database is healthy and ready to accept connections."""
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True  
        except OperationalError:
            if attempt < max_retries - 1:  
                time.sleep(retry_delay)
            else:
                return False

with app.app_context():
    engine = db.engine

    if not check_database_health(engine):
        raise Exception("Database connection failed. Unable to initialize the database.")

    db.create_all()

    if app.config.get("LOAD_LAYOUT"):
        layout = LayoutHandler.load_layout(app, app.config.get("LAYOUT_FILE"))
        items = LayoutHandler.load_items(app, app.config.get("ITEMS_FILE"))
        records = LayoutHandler.load_records(app, app.config.get("RECORD_FILE"))

    # Generate swagger.json in the same process to avoid a second Python startup
    app.config['SERVER_NAME'] = 'localhost:5000'
    _ = app.url_map  # Ensure all blueprints and namespaces are registered
    from storage_location_tracking.blueprints.api import api
    swagger_dict = api.__schema__
    with open('swagger.json', 'w') as f:
        json.dump(swagger_dict, f, indent=4)
    print('Swagger JSON saved successfully!')
    del app.config['SERVER_NAME']