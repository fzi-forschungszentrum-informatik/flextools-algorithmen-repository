from storage_location_tracking import create_app
import json

app = create_app()
app.config['SERVER_NAME'] = 'localhost:5000'

with app.app_context():
    # Ensure all blueprints and namespaces are registered 
    _ = app.url_map 

    from storage_location_tracking.blueprints.api import api

    swagger_dict = api.__schema__

    with open('swagger.json', 'w') as f:
        json.dump(swagger_dict, f, indent=4)

    print('Swagger JSON saved successfully!')

del app.config['SERVER_NAME']