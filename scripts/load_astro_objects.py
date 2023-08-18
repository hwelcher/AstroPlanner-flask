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

# Open the CSV file
with open('messier_catalog.csv', mode='r') as csv_file:
    reader = csv.DictReader(csv_file)
    
    # Iterate over each row
    for row in reader:
        # Append the row to the JSON list (no need to explicitly convert to JSON here)
        json_list.append(row)

for item in json_list:
    astro_objects_ref.add(item)
