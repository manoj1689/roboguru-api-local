from fastapi import APIRouter, HTTPException, Depends
from core.firebase_config import initialize_firebase
from firebase_admin import auth, messaging, exceptions
import jwt
from datetime import datetime, timedelta
from core.config import settings
from schemas import FirebaseLoginInput
from models import User
from database import get_db
from sqlalchemy.orm import Session
from datetime import timedelta
from services.auth import create_access_token, create_refresh_token
from services.classes import create_response
from schemas import NotificationRequest
from google.oauth2 import id_token
from google.auth.transport import requests
router = APIRouter()

# Initialize Firebase
initialize_firebase()
@router.post("/firebase-login")
async def firebase_login(input: FirebaseLoginInput, db: Session = Depends(get_db)):
    id_token_str = input.id_token

    if not id_token_str:
        return create_response(success=False, message="ID Token is required.")

    try:
        decoded_token = None
        try:
            decoded_token = auth.verify_id_token(id_token_str)
            print("Decoded Token (auth.verify_id_token):", decoded_token)
        except exceptions.FirebaseError:
            # Fallback to other verification method if the first fails
            decoded_token = id_token.verify_oauth2_token(
                id_token_str,
                requests.Request(),
                audience="709622863624-2itnt673s7u60inf39tsr37tgud8v653.apps.googleusercontent.com",
            )
            print("Decoded Token (id_token.verify_oauth2_token):", decoded_token)

        if not decoded_token:
            return create_response(success=False, message="Token verification failed.")

        # Step 2: Extract required information
        uid = decoded_token.get("uid") or decoded_token.get("sub")
        email = decoded_token.get("email")
        phone_number = decoded_token.get("phone_number")
        role = decoded_token.get("role", "normal")  # Default role
        identifier = phone_number or email

        print(f"UID: {uid}, Email: {email}, Phone Number: {phone_number}, Role: {role}")

        if not uid or not identifier:
            return create_response(
                success=False,
                message="Required fields missing: UID or identifier (email/phone).",
            )
        # Step 3: Check if the user exists by user_id, mobile_number, or email
        user = db.query(User).filter(
            (User.user_id == uid) | 
            (User.mobile_number == phone_number) | 
            (User.email == email)
        ).first()

        if user:
            # Check if the user_id matches the existing user's user_id
            if user.user_id != uid:
                return create_response(
                    success=False,
                    message=f"Conflict: The provided user_id '{uid}' conflicts with an existing user."
                )

            # Update the existing user's details
            user.email = email if email else user.email
            user.mobile_number = phone_number if phone_number else user.mobile_number
            user.user_identifier = identifier
            user.type = role
            user.updated_at = datetime.utcnow()
        else:
            # Create new user if none exists
            user = User(
                user_id=uid,
                email=email if email else None,
                mobile_number=phone_number,
                is_verified=True,
                user_identifier=identifier,
                type=role,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(user)

        # Commit the transaction
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            return create_response(success=False, message=f"Database error: {str(e)}")

        # Step 4: Generate JWT tokens
        jwt_access_token = create_access_token(data={"sub": identifier}, expires_delta=timedelta(hours=2))
        jwt_refresh_token = create_refresh_token(data={"sub": identifier})

        return create_response(
            success=True,
            message="Login successful.",
            data={
                "uid": uid,
                "email": email,
                "phone_number": phone_number,
                "user_identifier": identifier,
                "type": role,
                "access_token": jwt_access_token,
                "refresh_token": jwt_refresh_token,
                "token_type": "bearer",
            },
        )

    except (exceptions.FirebaseError, ValueError) as e:
        return create_response(success=False, message=f"Firebase error: {str(e)}")

    except Exception as e:
        return create_response(success=False, message=f"Unexpected error: {str(e)}")

# @router.post("/firebase-login")
# async def firebase_login(input: FirebaseLoginInput, db: Session = Depends(get_db)):
#     id_token = input.id_token  

#     if not id_token:
#         return create_response(
#             success=False,
#             message="ID Token is required."
#         )
#     try:
        # # Verify the Firebase ID token
        # decoded_token = auth.verify_id_token(id_token)
        # uid = decoded_token.get("uid")
        # phone_number = decoded_token.get("phone_number")

        # if not phone_number:
        #     return create_response(
        #         success=True,
        #         message="Phone number not available in token."
        #     )

#         # Check if user exists in the database
#         user = db.query(User).filter(User.mobile_number == phone_number).first()

#         if user:
#             # Update existing user details
#             user.updated_at = datetime.datetime.utcnow()
#             user.is_verified = True
#         else:
#             # Create new user record
#             user = User(
#                 user_id=uid,
#                 mobile_number=phone_number,
#                 is_verified=True,
#             )
#             db.add(user)

#         db.commit()

#         # Generate the access and refresh tokens
#         access_token_expires = timedelta(hours=2) 
#         jwt_access_token = create_access_token(
#             data={"sub": phone_number}, expires_delta=access_token_expires
#         )
#         jwt_refresh_token = create_refresh_token(
#             data={"sub": phone_number}
#         )  

#         return create_response(
#             success=True,
#             message="Login successful.",
#             data={
#                 "uid": uid,
#                 "phone_number": phone_number,
#                 "access_token": jwt_access_token,
#                 "refresh_token": jwt_refresh_token,
#                 "token_type": "bearer"
#             }
#         )

#     except Exception as e:
#         return create_response(
#             success=False,
#             message=f"Invalid ID Token: {str(e)}"
#         )


@router.post("/send-user-notification/")
async def send_user_notification(request: NotificationRequest, db: Session = Depends(get_db)):
    # Retrieve the FCM token associated with the provided UID
    user = db.query(User).filter(User.user_id == request.uid).first()

    if not user or not user.fcm_token:
        raise HTTPException(status_code=404, detail="FCM token not found for the provided UID")

    # Create a notification payload
    notification = messaging.Notification(
        title=request.title,
        body=request.body
    )

    # Create an FCM message
    message = messaging.Message(
        notification=notification,
        token=user.fcm_token,  # Send notification to the specific user's FCM token
        topic=request.topic  # Associate it with a topic
    )

    # Send the notification
    try:
        response = messaging.send(message)
        return {
            "message": "Notification sent successfully.",
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending notification: {str(e)}")

# @router.post("/send-notification/")
# async def send_notification(request: NotificationRequest, db: Session = Depends(get_db)):
#     # Retrieve the FCM token associated with the provided uid
#     user = db.query(User).filter(User.user_id == request.uid).first()

#     if not user or not user.fcm_token:
#         raise HTTPException(status_code=404, detail="FCM token not found for the provided UID")

#     # Define payloads based on operation type
#     payloads = {
#         "SUSPENDUSER": {
#             "OPERATION": "SUSPENDUSER",
#             "requestReason": "DEVICE LOST",
#             "requestReasonCode": "DEVICE_LOST",
#             "causedBy": "CARDHOLDER",
#             "TYPE": "Vts",
#             "SCHEMA": "Vts",
#             "INTEGRATOR": "SDK",
#             "previousTokenState": "ACTIVE"
#         },
#         "UPDATE_CARD_METADATA": {
#             "OPERATION": "UPDATE_CARD_METADATA",
#             "vProvisionedTokenID": "E7CE55BC8529E82D04CAF9793CE40C8C1EC9BB746F03",
#             "vPanEnrollmentId": "E7CE55BC8529E82D04CAF9793CE40C8C1EC9BB746F03",
#             "TYPE": "Vts",
#             "SCHEMA": "Vts",
#             "INTEGRATOR": "SDK",
#             "previousTokenState": "ACTIVE"
#         }
#     }

#     # Select payload based on the operation
#     if request.operation not in payloads:
#         raise HTTPException(status_code=400, detail="Invalid operation type")

#     payload = payloads[request.operation]

#     # Create FCM message
#     message = messaging.Message(
#         data=payload,
#         token=user.fcm_token,  # Use the FCM token retrieved from the database
#         android=messaging.AndroidConfig(priority="high", ttl=2160000)
#     )

#     # Send the notification
#     try:
#         response = messaging.send(message)
#         return {"message": "Notification sent successfully", "response": response}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error sending notification: {str(e)}")

# @router.post("/test")
# async def test_verify():
#     # Hard-coded ID token
#     hardcoded_id_token = (
#         "eyJhbGciOiJSUzI1NiIsImtpZCI6ImMwYTQwNGExYTc4ZmUzNGM5YTVhZGU5NTBhMjE2YzkwYjVkNjMwYjMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vcm9iby1ndXJ1IiwiYXVkIjoicm9iby1ndXJ1IiwiYXV0aF90aW1lIjoxNzM2MjcyNjUwLCJ1c2VyX2lkIjoieG5PRmZOWnJWZVNZd2JGTWZvQnhGRWozUFdLMiIsInN1YiI6InhuT0ZmTlpyVmVTWXdiRk1mb0J4RkVqM1BXSzIiLCJpYXQiOjE3MzYyNzI2NTEsImV4cCI6MTczNjI3NjI1MSwicGhvbmVfbnVtYmVyIjoiKzkxODc1MDg2MDY3NiIsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsicGhvbmUiOlsiKzkxODc1MDg2MDY3NiJdfSwic2lnbl9pbl9wcm92aWRlciI6InBob25lIn19.AAryrOcHpK90KXZ3VVEVRTJ2Ib21RDVBtu9yfUf7RsiYCyMQO9KOQ4OwzSqekctjvQ4hmxHb7k7k6G4NPoNDRyn3j-JGUeY48k0QtiUAJ9n3izOhDzIKdz94IIFXwbu6v645UoA3XoN2dDKinFcLuChwBTBjHIXJNvo_ORLmhNjMfm8fnjpvXMXtTqtdMdFklQ-nk7QkZjgz-UFgPJNofTfLPGFKaEsgaWELg0LtpKFNOrshOHKBAPexV8c8VtjxH-d--kNlvig_aeHRDkH-WTNBCPHwX4tTd3nvcKu3UeX3uhMd2O5H_3UioSsdT073ovfRuSoHfkH5CMtxTXm8Pg"
#     )

#     try:
#         # Verify the hard-coded ID token
#         decoded_token = auth.verify_id_token(hardcoded_id_token)
#         phone_number = decoded_token.get("phone_number")
#         uid = decoded_token.get("uid")

#         # Return the decoded token information
#         return {
#             "status": "success",
#             "uid": uid,
#             "phone_number": phone_number,
#             "decoded_token": decoded_token,
#         }
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=f"Invalid ID Token: {str(e)}")
