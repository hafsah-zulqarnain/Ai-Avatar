# config.py
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import storage

load_dotenv()

FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://console.cloud.google.com/firestore/databases/my-firestore-ai-avatar-db-6425ebf/data/panel?project=jetrr-hafsa-zulqarnain-1'
})
db = firestore.client()

storage_client = storage.Client.from_service_account_json(FIREBASE_CREDENTIALS_PATH)
bucket_name = os.getenv("BUCKET_NAME")
bucket = storage_client.bucket(bucket_name)

API_KEY = os.getenv("API_KEY")
