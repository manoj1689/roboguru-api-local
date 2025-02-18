import os
import json
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build Firebase credentials dictionary dynamically
firebase_credentials = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
    "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN"),
}

# Initialize Firebase Admin SDK
def initialize_firebase():
    try:
        if not firebase_admin._apps:  # Check if Firebase is not already initialized
            cred = credentials.Certificate(firebase_credentials)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin initialized successfully.")
        else:
            print("Firebase Admin already initialized.")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")

# Call the function
initialize_firebase()
