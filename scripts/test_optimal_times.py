import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import datetime
from google.cloud.firestore_v1.base_query import FieldFilter
import pytz

# List to hold the JSON objects
json_list = []

# Use a service account.
cred = credentials.Certificate('astroplanner-25d27-firebase-adminsdk-tv1sf-3516a4d7d5.json')

app = firebase_admin.initialize_app(cred)
db = firestore.client()

optimal_times_ref = db.collection("optimal_times")

compare_start_date = datetime.datetime.strptime("2023-08-01 00:00", '%Y-%m-%d %H:%M')
compare_end_date = datetime.datetime.strptime("2023-08-24 12:00", '%Y-%m-%d %H:%M')

compare_start_date_utc = pytz.utc.localize(compare_start_date)
compare_end_date_utc = pytz.utc.localize(compare_end_date)

# Query for documents where the field starts with the given value
# TODO: Update this to include start_date AND end_date as the first case.
query_ref = optimal_times_ref.where(filter=FieldFilter("start_date", "==", compare_start_date_utc)).where("latitude", "==", 43.4494).where("longitude", "==", -80.5752)

results = query_ref.stream()
results_list = list(results)

if not results_list:
    print("No Results.")
    # TODO: Generate new results here
else:
    for doc in results_list:
        print(f'{doc.id} => {doc.to_dict()}')

# else:
#     # Check if end date is also within the window
#     for doc in results_list:
#         end_date = doc.to_dict()["end_date"]

#         if end_date >= compare_end_date_utc:
#             print("End date in range")
#             # TODO: Extract the optimal times to a new list and return them
#         else:
#             print(f'End date not in range: {doc.to_dict()["end_date"]}')
#             # TODO: 

# for doc in results:
#     print(f'{doc.id} => {doc.to_dict()}')