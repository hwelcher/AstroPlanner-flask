from astropy.time import Time
from flask import Flask, g, request, jsonify
from flask_compress import Compress
from flask_cors import CORS
import firebase_admin
from google.cloud.firestore_v1.base_query import FieldFilter
from firebase_admin import credentials
from firebase_admin import firestore
from utilities import time_utils
from utilities import target_utils
import datetime
import pytz
import re

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

    # @app.route('/search_objects', methods=['GET'])
    # def search_objects():
    #     query = request.args.get('query', '').strip()

    #     astro_objects_ref = g.db.collection("astro_objects")

    #     # The field and value you're querying for
    #     field_name = 'primary_identifier'

    #     # Query for documents where the field starts with the given value
    #     query_ref = astro_objects_ref.order_by(field_name) \
    #                             .start_at({field_name: query}) \
    #                             .end_at({field_name: query + '\uf8ff'})

    #     # Execute the query and print the results
    #     astro_objects = query_ref.stream()

    #     suggestions = []

    #     for obj in astro_objects:
    #         obj_dict = obj.to_dict()
    #         suggestions.append(
    #             {
    #                 "id": obj_dict["id"],
    #                 "primary_identifier": obj_dict["primary_identifier"],
    #                 "display_name": f'{obj_dict["primary_identifier"]} - {obj_dict["object_name"]}' if obj_dict["object_name"] else obj_dict["primary_identifier"]
    #             }
    #         )
    #     return jsonify(suggestions)

    def query_objects_by_id(field_name, field_value):
        astro_objects_ref = g.db.collection("astro_objects_full")

        query_ref = astro_objects_ref.where(filter=FieldFilter(field_name, "==", field_value))

        # Execute the query and print the results
        astro_objects = query_ref.stream()

        suggestions = []

        for obj in astro_objects:
            obj_dict = obj.to_dict()

            object_name = obj_dict["object_name"].split(',')[0] if obj_dict["object_name"] else None
            suggestions.append(
                {
                    "id": field_value,
                    "display_name": f'{field_value} - {object_name}' if object_name else field_value
                }
            )
        return suggestions

    def query_objects_by_name(name):
        astro_objects_ref = g.db.collection("astro_objects_full")

        # The field name for object_name
        field_name = 'object_name'

        # Query for documents where the field starts with the given value
        query_ref = astro_objects_ref.order_by(field_name) \
                                .start_at({field_name: name}) \
                                .end_at({field_name: name + '\uf8ff'})

        # Execute the query and print the results
        astro_objects = query_ref.stream()

        suggestions = []

        for obj in astro_objects:
            obj_dict = obj.to_dict()

            object_name = obj_dict["object_name"].split(',')[0] if obj_dict["object_name"] else None

            messier_id = obj_dict["messier_id"]
            ngc_id = obj_dict["ngc_id"]
            ic_id = obj_dict["ic_id"]

            id_value = None

            if messier_id:
                id_value = messier_id
            elif ngc_id:
                id_value = ngc_id
            elif ic_id:
                id_value = ic_id            

            suggestions.append(
                {
                    "id": id_value,
                    "display_name": f'{id_value} - {object_name}'
                }
            )
        return suggestions

    def query_objects_by_keyword(name):
        astro_objects_ref = g.db.collection("astro_objects_full")

        # Keyword field names
        keywords = [
            'keyword_01',
            'keyword_02',
            'keyword_03',
            'keyword_04',
            'keyword_05',
            'keyword_06',
            'keyword_07'
        ]

        suggestions = []

        for keyword in keywords:
            # Query for documents where the field starts with the given value
            query_ref = astro_objects_ref.order_by(keyword) \
                                    .start_at({keyword: name.lower()}) \
                                    .end_at({keyword: name.lower() + '\uf8ff'})

            # Execute the query and print the results
            astro_objects = query_ref.stream()

            for obj in astro_objects:
                obj_dict = obj.to_dict()

                object_name = obj_dict["object_name"].split(',')[0] if obj_dict["object_name"] else None

                messier_id = obj_dict["messier_id"]
                ngc_id = obj_dict["ngc_id"]
                ic_id = obj_dict["ic_id"]

                id_value = None

                if messier_id:
                    id_value = messier_id
                elif ngc_id:
                    id_value = ngc_id
                elif ic_id:
                    id_value = ic_id            

                suggestions.append(
                    {
                        "id": id_value,
                        "display_name": f'{id_value} - {object_name}'
                    }
                )

        # suggestions = list(set(suggestions))

        return suggestions

    @app.route('/search_objects', methods=['GET'])
    def search_objects():
        query = request.args.get('query', '').strip()

        astro_objects_ref = g.db.collection("astro_objects_full")

        # TODO: Figure out which identifier to use
        # Identifier format could be IC123, IC-123, IC 123, NGC321, NGC-321, NGC 321, M31, M-31, M 31
        # If no identifier match, fallback to common name

        identifier_pattern = r'\b(IC|NGC|M)[\s\-]?(\d+)\b'

        matches = re.findall(identifier_pattern, query)

        suggestions = []

        # Check if we have an identifier
        if matches:
            prefix = matches[0][0]
            number = matches[0][1]

            if prefix == "IC":
                # Query for IC object
                suggestions = query_objects_by_id("ic_id", f"{prefix}{number}")
            elif prefix == "NGC":
                # Query for NGC object
                suggestions = query_objects_by_id("ngc_id", f"{prefix}{number}")
            elif prefix == "M":
                # Query for M object
                suggestions = query_objects_by_id("messier_id", f"{prefix}{number}")
        else:
            suggestions = query_objects_by_keyword(query)

        return jsonify(suggestions)

    CORS(app)       # Enable CORS for all routes

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
