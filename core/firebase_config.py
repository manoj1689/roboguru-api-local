import firebase_admin
from firebase_admin import credentials

# Initialize Firebase Admin SDK
def initialize_firebase():
    try:
<<<<<<< HEAD
        cred = credentials.Certificate("/home/nasir/workspace/eramlabs/robo_guru/roboguru_api/robo-guru-firebase-adminsdk-qch2e-a9083614a2.json")
=======
        cred = credentials.Certificate("robo-guru-firebase-adminsdk-qch2e-a9083614a2.json")
>>>>>>> 69e201c15e1ea3e67d506f65ebbcef1ffa53f361
        firebase_admin.initialize_app(cred)
        print("Firebase Admin initialized successfully.")
    except ValueError:
        print("Firebase Admin already initialized.")

