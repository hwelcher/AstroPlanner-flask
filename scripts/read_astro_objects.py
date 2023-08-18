import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import csv

# List to hold the JSON objects
json_list = []

# Use a service account.
cred = credentials.Certificate('astroplanner-25d27-firebase-adminsdk-tv1sf-3516a4d7d5.json')

app = firebase_admin.initialize_app(cred)
db = firestore.client()

astro_objects_ref = db.collection("astro_objects")

# The field and value you're querying for
field_name = 'primary_identifier'
starts_with_value = 'M3'

# Query for documents where the field starts with the given value
query_ref = astro_objects_ref.order_by(field_name) \
                        .start_at({field_name: starts_with_value}) \
                        .end_at({field_name: starts_with_value + '\uf8ff'})

# Execute the query and print the results
docs = query_ref.stream()
for doc in docs:
    print(doc.to_dict()["primary_identifier"])

# astro_objects = astro_objects_ref.stream()

# for astro_object in astro_objects:
#     print(f"{astro_object.id} => {astro_object.to_dict()}")


