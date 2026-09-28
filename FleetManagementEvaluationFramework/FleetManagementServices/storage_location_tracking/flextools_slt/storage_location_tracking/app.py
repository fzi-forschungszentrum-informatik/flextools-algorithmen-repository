from flask import Flask, request, jsonify
from models import db, InventoryHistory

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri'
db.init_app(app)

@app.route('/inventory_history', methods=['GET'])
def get_inventory_history():
    """
    Endpoint to query the InventoryHistory table based on provided parameters.
    """
    id = request.args.get('id')
    item_id = request.args.get('item_id')
    timestamp = request.args.get('timestamp')

    if timestamp:
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except ValueError:
            return jsonify({"error": "Invalid timestamp format. Use ISO format."}), 400

    result = InventoryHistory.query_inventory_history(id=id, item_id=item_id, timestamp=timestamp)

    if isinstance(result, list):
        return jsonify([record.to_dict() for record in result])
    elif result:
        return jsonify(result.to_dict())
    else:
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
