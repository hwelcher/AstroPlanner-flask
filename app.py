from astropy.time import Time
from flask import Flask, g, request, jsonify
from flask_compress import Compress
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from utilities import time_utils
from utilities import target_utils
import datetime
import pytz

# Use a service account.
cred = credentials.Certificate('astroplanner-25d27-firebase-adminsdk-tv1sf-3516a4d7d5.json')
firebase_admin.initialize_app(cred)

def create_app():
    app = Flask(__name__)
    Compress(app)   # Enable compression for all routes

    @app.before_request
    def before_request():
        if 'db' not in g:
            g.db = firestore.client()

    @app.teardown_appcontext
    def teardown_db(exception=None):
        db = g.pop('db', None)

    @app.route('/test', methods=['GET'])
    def test():
        # Get optimal times to shoot target

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')
        location_name = request.args.get('location_name')
        target_id = request.args.get('target_id')
        target_name = request.args.get('target_name')
        min_altitude = request.args.get('min_altitude')
        min_session_length = request.args.get('min_session_length')

        try:
            optimal_target_times = target_utils.get_optimal_target_times(start_date_str, end_date_str, latitude, longitude, location_name, target_id, target_name, min_altitude, min_session_length)
            return optimal_target_times

        except ValueError as e:
            return jsonify({'error': str(e)}), 400       

    @app.route('/get_optimal_target_times', methods=['GET'])
    def get_optimal_target_times():
        # Get optimal times to shoot target

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')
        location_name = request.args.get('location_name')
        target_id = request.args.get('target_id')
        target_name = request.args.get('target_name')
        min_altitude = request.args.get('min_altitude')
        min_session_length = request.args.get('min_session_length')

        try:
            optimal_target_times = target_utils.get_optimal_target_times(start_date_str, end_date_str, latitude, longitude, location_name, target_id, target_name, min_altitude, min_session_length)
            return optimal_target_times

        except ValueError as e:
            return jsonify({'error': str(e)}), 400       


    @app.route('/get_optimal_times', methods=['GET'])
    def get_optimal_times():
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')
        local_timezone_str = request.args.get('local_timezone')

        try:
            local_timezone = pytz.timezone(local_timezone_str)
            start_date_obj = datetime.datetime.strptime(start_date_str, '%Y-%m-%d %H:%M')
            end_date_obj = datetime.datetime.strptime(end_date_str, '%Y-%m-%d %H:%M')

            # Assume start_date_obj and end_date_obj are in UTC
            start_date_utc = pytz.utc.localize(start_date_obj)
            end_date_utc = pytz.utc.localize(end_date_obj)

            latitude = float(latitude)
            longitude = float(longitude)

            optimal_times = time_utils.get_or_generate_optimal_times(start_date_utc, end_date_utc, latitude, longitude)

            times_iso = []

            # Convert the Astropy Time objects to datetime objects in UTC and then to the local timezone
            optimal_times_local = [pytz.utc.localize(time.datetime).astimezone(local_timezone) for time in optimal_times]

            # Format the times to the required ISO format without the offset
            times_iso += [time.strftime('%Y-%m-%dT%H:%M:%S.000') for time in optimal_times_local]

            return jsonify(times_iso)

        except ValueError as e:
            return jsonify({'error': str(e)}), 400

    @app.route('/generate_optimal_times', methods=['POST'])
    def generate_optimal_times():
        start_date_str = request.json.get('start_date')
        end_date_str = request.json.get('end_date')
        latitude = request.json.get('latitude')
        longitude = request.json.get('longitude')

        try:
            start_date_obj = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date_obj = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')

            # Assume start_date_obj and end_date_obj are in UTC
            start_date_utc = pytz.utc.localize(start_date_obj)
            end_date_utc = pytz.utc.localize(end_date_obj)

            latitude = float(latitude)
            longitude = float(longitude)

            time_utils.generate_optimal_times_full(start_date_utc, end_date_utc, latitude, longitude)

        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        response = {
            "status": "success",
            "message": "Optimal times generated successfully"
        }
        return jsonify(response), 200

    @app.route('/search_objects', methods=['GET'])
    def search_objects():
        query = request.args.get('query', '').strip()

        astro_objects_ref = g.db.collection("astro_objects")

        # The field and value you're querying for
        field_name = 'primary_identifier'

        # Query for documents where the field starts with the given value
        query_ref = astro_objects_ref.order_by(field_name) \
                                .start_at({field_name: query}) \
                                .end_at({field_name: query + '\uf8ff'})

        # Execute the query and print the results
        astro_objects = query_ref.stream()

        suggestions = []

        for obj in astro_objects:
            obj_dict = obj.to_dict()
            suggestions.append(
                {
                    "id": obj_dict["id"],
                    "primary_identifier": obj_dict["primary_identifier"],
                    "display_name": f'{obj_dict["primary_identifier"]} - {obj_dict["object_name"]}' if obj_dict["object_name"] else obj_dict["primary_identifier"]
                }
            )
        return jsonify(suggestions)

    CORS(app)       # Enable CORS for all routes

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
