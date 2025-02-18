from fastapi import APIRouter, HTTPException, Depends, status
from core.firebase_config import initialize_firebase
from firebase_admin import auth, exceptions, messaging
from jose import JWTError, jwt
from datetime import datetime, timedelta
from core.config import settings
from schemas.firebase import FirebaseLoginInput
from schemas.token import TokenRequest
from schemas.notification import NotificationRequest
from models.user import User
from database import get_db
from sqlalchemy.orm import Session
from utils.auth import create_access_token, create_refresh_token
from utils.response import create_response
from google.oauth2 import id_token
from google.auth.transport import requests
import psycopg2

router = APIRouter()

initialize_firebase()

# SUPERADMIN_UID = "xnOFfNZrVeSYwbFMfoBxFEj3PWK2" 

@router.post("/firebase-login")
async def firebase_login(input: FirebaseLoginInput, db: Session = Depends(get_db)):
    id_token_str = input.id_token
    
    if not id_token_str:
        return create_response(success=False, message="ID Token is required.")

    try:
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

        uid = decoded_token.get("uid") or decoded_token.get("sub")
        email = decoded_token.get("email")
        phone_number = decoded_token.get("phone_number")
        role = decoded_token.get("role", "normal")
        identifier = phone_number or email

        if not uid or not identifier:
            return create_response(
                success=False,
                message="Required fields missing: UID or identifier (email/phone).",
            )

        user = db.query(User).filter(
            (User.user_id == uid) | (User.user_identifier == identifier)
        ).first()

        if user:
            if user.education_level and user.user_class:
                jwt_access_token = create_access_token(data={"sub": str(user.user_identifier)}, expires_delta=timedelta(hours=200))
                jwt_refresh_token = create_refresh_token(data={"sub": str(user.user_identifier)})

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

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            if isinstance(e.orig, psycopg2.errors.UniqueViolation):
                user = db.query(User).filter(User.user_identifier == identifier).first()
            else:
                return create_response(success=False, message=f"Database error: {str(e)}")

        jwt_access_token = create_access_token(data={"sub": str(user.user_identifier)}, expires_delta=timedelta(hours=200))
        jwt_refresh_token = create_refresh_token(data={"sub": str(user.user_identifier)})

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

    notification = messaging.Notification(
        title=request.title,
        body=request.body
    )

    message = messaging.Message(
        notification=notification,
        token=user.fcm_token, 
        topic=request.topic  
    )

    try:
        response = messaging.send(message)
        return {
            "message": "Notification sent successfully.",
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending notification: {str(e)}")
    
@router.post("/superadmin/login")
async def superadmin_login(input: FirebaseLoginInput, db: Session = Depends(get_db)):
    id_token_str = input.id_token

    if not id_token_str:
        return create_response(success=False, message="ID Token is required.")

    try:
        decoded_token = None
        try:
            decoded_token = auth.verify_id_token(id_token_str)
        except exceptions.FirebaseError:
            decoded_token = id_token.verify_oauth2_token(
                id_token_str,
                requests.Request(),
                audience=settings.FIREBASE_CLIENT_ID,
            )

        if not decoded_token:
            return create_response(success=False, message="Token verification failed.")

        uid = decoded_token.get("uid") or decoded_token.get("sub")
        email = decoded_token.get("email")
        phone_number = decoded_token.get("phone_number")
        identifier = phone_number or email

        if uid != settings.SUPERADMIN_UID:
            return create_response(success=False, message="Unauthorized access. Only superadmin can login.")

        user = db.query(User).filter(User.user_id == uid).first()

        if not user:
            user = User(
                user_id=uid,
                email=email,
                mobile_number=phone_number,
                is_verified=True,
                user_identifier=identifier,
                type="superadmin",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(user)
            db.commit()
        else:
            user.type = "superadmin" 
            db.commit()

        jwt_access_token = create_access_token(data={"sub": str(user.user_identifier), "role": "superadmin"}, expires_delta=timedelta(hours=200))
        jwt_refresh_token = create_refresh_token(data={"sub": str(user.user_identifier)})

        return create_response(
            success=True,
            message="Superadmin login successful.",
            data={
                "uid": user.user_id,
                "email": user.email,
                "phone_number": user.mobile_number,
                "user_identifier": user.user_identifier,
                "type": "superadmin",
                "access_token": jwt_access_token,
                "refresh_token": jwt_refresh_token,
                "token_type": "bearer",
            },
        )

    except (exceptions.FirebaseError, ValueError) as e:
        return create_response(success=False, message=f"Firebase error: {str(e)}")
    except Exception as e:
        return create_response(success=False, message=f"Unexpected error: {str(e)}")
