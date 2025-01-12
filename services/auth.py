from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import JWTError, jwt, ExpiredSignatureError
from core.config import settings
from models import User
from sqlalchemy.orm import Session
from database import get_db
from services.classes import create_response
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7)) 
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        # Decode the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print(f"Decoded payload: {payload}")
        mobile_number = payload.get("sub")
        
        if not mobile_number:
            return create_response(success=False, message="Invalid token or token expired.")
        
        print(f"Searching for user with mobile_number: {mobile_number}")
        
        # Query user in the database
        user = db.query(User).filter(User.mobile_number == mobile_number).first()
        if not user:
            return create_response(success=False, message="User not found.")
        
        return user
    except ExpiredSignatureError:
        return create_response(success=False, message="Token has expired.")
    except JWTError:
        return create_response(success=False, message="Invalid token.")