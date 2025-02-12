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

initialize_firebase()

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
                        "name": user.name,
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
        token=user.fcm_token, 
        topic=request.topic  
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
