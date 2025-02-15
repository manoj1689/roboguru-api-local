import firebase_admin
from firebase_admin import credentials, messaging

# Path to your service account key JSON file
cred = credentials.Certificate("comviva-hce-demo-firebase-adminsdk-ko0c5-024af7284b.json")

# Initialize the app with a service account
firebase_admin.initialize_app(cred)

 
def send_test_notification(token):

    # Payload structure SUSPENDUSER,UNSUSPENDUSER,DELETEUSER
    payloadV1 = {
        "OPERATION": "SUSPENDUSER",
        "requestReason": "DEVICE LOST",
        "requestReasonCode": "DEVICE_LOST",
        "causedBy": "CARDHOLDER",
        "TYPE": "Vts", 
        "SCHEMA": "Vts",
        "INTEGRATOR": "SDK", 
        "previousTokenState": "ACTIVE"
    }

    payloadV2 = {
        "OPERATION": "UPDATE_CARD_METADATA",
        "vProvisionedTokenID": "E7CE55BC8529E82D04CAF9793CE40C8C1EC9BB746F03",
        "vPanEnrollmentId":"E7CE55BC8529E82D04CAF9793CE40C8C1EC9BB746F03",
        "TYPE": "Vts", 
        "SCHEMA": "Vts",
        "INTEGRATOR": "SDK", 
        "previousTokenState": "ACTIVE"
    }


    payloadV3 = {
        "OPERATION": "UPDATE_TXN_HISTORY",
        "vProvisionedTokenID": "E7CE55BC8529E82D04CAF9793CE40C8C1EC9BB746F03",
        "vPanEnrollmentId":"E7CE55BC8529E82D04CAF9793CE40C8C1EC9BB746F03",
        "TYPE": "Vts", 
        "SCHEMA": "Vts",
        "INTEGRATOR": "SDK", 
        "previousTokenState": "ACTIVE"
    }

    payloadV4 = {
        "OPERATION": "TOKEN_STATUS_UPDATED",
        "vProvisionedTokenID": "E7CE55BC8529E82D04CAF9793CE40C8C1EC9BB746F03",
        "TYPE": "Vts", 
        "SCHEMA": "Vts",
        "INTEGRATOR": "SDK", 
        "previousTokenState": "ACTIVE"
    }

    # Define the FCM message payload
    message = messaging.Message(
        data=payloadV1, 
        token=token,  
        android=messaging.AndroidConfig(
            priority="high",
            ttl=2160000  # Time-to-live in milliseconds
        )
    )

    print('message:', message)

    # Send a message to the device corresponding to the provided registration token
    try:
        response = messaging.send(message)
        print('Successfully sent message:', response)
    except Exception as e:
        print('Error sending message:', str(e))



token = "cG276FMFq0wnvFinFh6cZg:APA91bGFh8t-PUj8f7bWApqWAb7tjA9mVF10UcHqh3PYJbzh9KX41K0GmwNoGMvFvxqwmbNCsl85pbO-CtI9hjFbJ5q1ooBvRynwaymscvjU9_q8qr6B5bo"
send_test_notification(token)

 