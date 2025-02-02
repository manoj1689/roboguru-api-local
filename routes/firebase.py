from fastapi import APIRouter, HTTPException, Depends, status
from core.firebase_config import initialize_firebase
from firebase_admin import auth, messaging, exceptions
from jose import JWTError, jwt
from datetime import datetime, timedelta
from core.config import settings
from schemas import FirebaseLoginInput, TokenRequest
from models import User
from database import get_db
from sqlalchemy.orm import Session
from datetime import timedelta
from services.auth import create_access_token, create_refresh_token
from services.classes import create_response
from schemas import NotificationRequest
from google.oauth2 import id_token
from google.auth.transport import requests
import psycopg2

router = APIRouter()

# Initialize Firebase
initialize_firebase()


# @router.post("/firebase-login")
# async def firebase_login(input: FirebaseLoginInput, db: Session = Depends(get_db)):
#     id_token_str = input.id_token

#     if not id_token_str:
#         return create_response(success=False, message="ID Token is required.")

#     try:
#         # Step 1: Verify ID Token
#         decoded_token = None
#         try:
#             decoded_token = auth.verify_id_token(id_token_str)
#         except exceptions.FirebaseError:
#             decoded_token = id_token.verify_oauth2_token(
#                 id_token_str,
#                 requests.Request(),
#                 audience="709622863624-2itnt673s7u60inf39tsr37tgud8v653.apps.googleusercontent.com",
#             )

#         if not decoded_token:
#             return create_response(success=False, message="Token verification failed.")

#         # Step 2: Extract required information
#         uid = decoded_token.get("uid") or decoded_token.get("sub")
#         email = decoded_token.get("email")
#         phone_number = decoded_token.get("phone_number")
#         role = decoded_token.get("role", "normal")  # Default role
#         identifier = phone_number or email

#         # Log extracted information
#         print(f"Decoded Token: {decoded_token}")
#         print(f"UID: {uid}, Email: {email}, Phone Number: {phone_number}, Role: {role}")

#         if not uid or not identifier:
#             return create_response(
#                 success=False,
#                 message="Required fields missing: UID or identifier (email/phone).",
#             )

#         # Step 3: Check user existence
#         user = db.query(User).filter(
#             (User.user_id == uid) | (User.user_identifier == identifier)
#         ).first()

#         if user:
#             # Update existing user
#             user.email = email if email else user.email
#             user.mobile_number = phone_number if phone_number else user.mobile_number
#             user.updated_at = datetime.utcnow()
#         else:
#             # Create new user
#             user = User(
#                 user_id=uid,
#                 email=email if email else None,
#                 mobile_number=phone_number,
#                 is_verified=True,
#                 user_identifier=identifier,
#                 type=role,
#                 created_at=datetime.utcnow(),
#                 updated_at=datetime.utcnow(),
#             )
#             db.add(user)

#         # Commit changes
#         try:
#             db.commit()
#         except Exception as e:
#             db.rollback()
#             if isinstance(e.orig, psycopg2.errors.UniqueViolation):
#                 user = db.query(User).filter(User.user_identifier == identifier).first()
#             else:
#                 return create_response(success=False, message=f"Database error: {str(e)}")

#         # Step 4: Generate tokens
#         jwt_access_token = create_access_token(data={"sub": str(user.user_identifier),}, expires_delta=timedelta(hours=200))
#         jwt_refresh_token = create_refresh_token(data={"sub": str(user.user_identifier),})

#         # Step 5: Return response
#         return create_response(
#             success=True,
#             message="Login successful.",
#             data={
#                 "uid": user.user_id,
#                 "email": user.email,
#                 "phone_number": user.mobile_number,
#                 "user_identifier": user.user_identifier,
#                 "type": user.type,
#                 "access_token": jwt_access_token,
#                 "refresh_token": jwt_refresh_token,
#                 "token_type": "bearer",
#             },
#         )

#     except (exceptions.FirebaseError, ValueError) as e:
#         return create_response(success=False, message=f"Firebase error: {str(e)}")

#     except Exception as e:
#         return create_response(success=False, message=f"Unexpected error: {str(e)}")



@router.post("/firebase-login")
async def firebase_login(input: FirebaseLoginInput, db: Session = Depends(get_db)):
    id_token_str = input.id_token

    if not id_token_str:
        return create_response(success=False, message="ID Token is required.")

    try:
        # Step 1: Verify ID Token
        decoded_token = None
        try:
            decoded_token = auth.verify_id_token(id_token_str)
        except exceptions.FirebaseError:
            decoded_token = id_token.verify_oauth2_token(
                id_token_str,
                requests.Request(),
                audience="709622863624-2itnt673s7u60inf39tsr37tgud8v653.apps.googleusercontent.com",
            )

        if not decoded_token:
            return create_response(success=False, message="Token verification failed.")

        # Step 2: Extract required information
        uid = decoded_token.get("uid") or decoded_token.get("sub")
        email = decoded_token.get("email")
        phone_number = decoded_token.get("phone_number")
        role = decoded_token.get("role", "normal")  # Default role
        identifier = phone_number or email

        # Log extracted information
        print(f"Decoded Token: {decoded_token}")
        print(f"UID: {uid}, Email: {email}, Phone Number: {phone_number}, Role: {role}")

        if not uid or not identifier:
            return create_response(
                success=False,
                message="Required fields missing: UID or identifier (email/phone).",
            )

        # Step 3: Check user existence
        user = db.query(User).filter(
            (User.user_id == uid) | (User.user_identifier == identifier)
        ).first()

        if user:
            # Check if education_id and class_id are saved
            if user.education_level and user.user_class:
                jwt_access_token = create_access_token(data={"sub": str(user.user_identifier),}, expires_delta=timedelta(hours=200))
                jwt_refresh_token = create_refresh_token(data={"sub": str(user.user_identifier),})

                # Profile is updated
                return create_response(
                    success=True,
                    profile_updated=True,
                    message="Login successful.",
                    data={
                        "uid": user.user_id,
                        "email": user.email,
                        "phone_number": user.mobile_number,
                        "user_identifier": user.user_identifier,
                        "type": user.type,
                        "access_token": jwt_access_token,
                        "refresh_token": jwt_refresh_token,
                        "token_type": "bearer",
                        "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
                        "occupation": user.occupation,
                        "education_level": user.education_level,
                        "user_class": user.user_class,
                        "language": user.language,
                        "profile_image": user.profile_image,
                    },
                )
        else:
            # Create new user if not found
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

        # Commit changes
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                user = db.query(User).filter(User.user_identifier == identifier).first()
            else:
                return create_response(success=False, message=f"Database error: {str(e)}")

        # Step 4: Generate tokens
        jwt_access_token = create_access_token(data={"sub": str(user.user_identifier),}, expires_delta=timedelta(hours=200))
        jwt_refresh_token = create_refresh_token(data={"sub": str(user.user_identifier),})

        # Step 5: Return response
        return create_response(
            success=True,
            profile_updated=False,
            message="Profile not updated. Missing education or class details.",
            data={
                "uid": user.user_id,
                "email": user.email,
                "phone_number": user.mobile_number,
                "user_identifier": user.user_identifier,
                "type": user.type,
                "access_token": jwt_access_token,
                "refresh_token": jwt_refresh_token,
                "token_type": "bearer",
            },
        )

    except (exceptions.FirebaseError, ValueError) as e:
        return create_response(success=False, message=f"Firebase error: {str(e)}")

    except Exception as e:
        return create_response(success=False, message=f"Unexpected error: {str(e)}")





@router.post("/token/refresh")
def refresh_token(request: TokenRequest, db: Session = Depends(get_db)):
    token = request.refresh_token
    if not token:
        return create_response(
            success=False,
            message="Refresh token is required."
        )

    try:
        # Decode the refresh token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_identifier = payload.get("sub")
        
        if not user_identifier:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user = db.query(User).filter(User.user_identifier == user_identifier).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        access_token = create_access_token(data={"sub": user.user_identifier, "role": user.type})

        return create_response(
            success=True,
            message="Access token successfully refreshed.",
            data={
                "access_token": access_token,
                "token_type": "bearer"
            }
        )

    except JWTError:
        return create_response(
            success=False,
            message="Invalid refresh token."
        )


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
