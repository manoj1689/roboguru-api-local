from fastapi import APIRouter, HTTPException, Depends
from core.firebase_config import initialize_firebase
from firebase_admin import auth
import jwt
import datetime
from core.config import settings
from schemas import FirebaseLoginInput
from models import User
from database import get_db
from sqlalchemy.orm import Session
from datetime import timedelta
from services.auth import create_access_token, create_refresh_token
from services.classes import create_response

router = APIRouter()

# Initialize Firebase
initialize_firebase()

@router.post("/verify-otp")
async def test_verify():
    # Hard-coded ID token
    hardcoded_id_token = (
        "eyJhbGciOiJSUzI1NiIsImtpZCI6ImMwYTQwNGExYTc4ZmUzNGM5YTVhZGU5NTBhMjE2YzkwYjVkNjMwYjMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vcm9iby1ndXJ1IiwiYXVkIjoicm9iby1ndXJ1IiwiYXV0aF90aW1lIjoxNzM2MjcyNjUwLCJ1c2VyX2lkIjoieG5PRmZOWnJWZVNZd2JGTWZvQnhGRWozUFdLMiIsInN1YiI6InhuT0ZmTlpyVmVTWXdiRk1mb0J4RkVqM1BXSzIiLCJpYXQiOjE3MzYyNzI2NTEsImV4cCI6MTczNjI3NjI1MSwicGhvbmVfbnVtYmVyIjoiKzkxODc1MDg2MDY3NiIsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsicGhvbmUiOlsiKzkxODc1MDg2MDY3NiJdfSwic2lnbl9pbl9wcm92aWRlciI6InBob25lIn19.AAryrOcHpK90KXZ3VVEVRTJ2Ib21RDVBtu9yfUf7RsiYCyMQO9KOQ4OwzSqekctjvQ4hmxHb7k7k6G4NPoNDRyn3j-JGUeY48k0QtiUAJ9n3izOhDzIKdz94IIFXwbu6v645UoA3XoN2dDKinFcLuChwBTBjHIXJNvo_ORLmhNjMfm8fnjpvXMXtTqtdMdFklQ-nk7QkZjgz-UFgPJNofTfLPGFKaEsgaWELg0LtpKFNOrshOHKBAPexV8c8VtjxH-d--kNlvig_aeHRDkH-WTNBCPHwX4tTd3nvcKu3UeX3uhMd2O5H_3UioSsdT073ovfRuSoHfkH5CMtxTXm8Pg"
    )

    try:
        # Verify the hard-coded ID token
        decoded_token = auth.verify_id_token(hardcoded_id_token)
        phone_number = decoded_token.get("phone_number")
        uid = decoded_token.get("uid")

        # Return the decoded token information
        return {
            "status": "success",
            "uid": uid,
            "phone_number": phone_number,
            "decoded_token": decoded_token,
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid ID Token: {str(e)}")
    

@router.post("/firebase-login")
async def firebase_login(input: FirebaseLoginInput, db: Session = Depends(get_db)):
    id_token = input.id_token  

    if not id_token:
        return create_response(
            success=False,
            message="ID Token is required."
        )
    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token.get("uid")
        phone_number = decoded_token.get("phone_number")

        if not phone_number:
            return create_response(
                success=True,
                message="Phone number not available in token."
            )

        # Check if user exists in the database
        user = db.query(User).filter(User.mobile_number == phone_number).first()

        if user:
            # Update existing user details
            user.updated_at = datetime.datetime.utcnow()
            user.is_verified = True
        else:
            # Create new user record
            user = User(
                user_id=uid,
                mobile_number=phone_number,
                is_verified=True,
            )
            db.add(user)

        db.commit()

        # Generate the access and refresh tokens
        access_token_expires = timedelta(hours=2) 
        jwt_access_token = create_access_token(
            data={"sub": phone_number}, expires_delta=access_token_expires
        )
        jwt_refresh_token = create_refresh_token(
            data={"sub": phone_number}
        )  

        return create_response(
            success=True,
            message="Login successful.",
            data={
                "uid": uid,
                "phone_number": phone_number,
                "access_token": jwt_access_token,
                "refresh_token": jwt_refresh_token,
                "token_type": "bearer"
            }
        )

    except Exception as e:
        return create_response(
            success=False,
            message=f"Invalid ID Token: {str(e)}"
        )