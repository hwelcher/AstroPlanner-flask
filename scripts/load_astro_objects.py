import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import csv

def add_keywords(obj):
    object_names = obj["object_name"].split(",")

    keywords = []
    for name in object_names:
        keywords += name.split(" ")

    # Remove duplicates
    keywords = list(set(keywords))

    for index, keyword in enumerate(keywords):
        obj[f"keyword_0{index+1}"] = keyword.lower()

    return obj

# List to hold the JSON objects
json_list = []

# Use a service account.
cred = credentials.Certificate('astroplanner-25d27-firebase-adminsdk-tv1sf-3516a4d7d5.json')

app = firebase_admin.initialize_app(cred)

db = firestore.client()

astro_objects_ref = db.collection("astro_objects_full")

# Open the CSV file
with open('full_catalog.csv', mode='r') as csv_file:
    reader = csv.DictReader(csv_file)

    obj = None

    # Iterate over each row
    for row in reader:
        obj = row
        if obj["object_name"]:
            obj = add_keywords(obj)

        # Append the row to the JSON list (no need to explicitly convert to JSON here)
        json_list.append(obj)

for item in json_list:
    astro_objects_ref.add(item)
