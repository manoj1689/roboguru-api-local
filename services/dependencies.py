from fastapi import Depends, HTTPException, status
from services.auth import get_current_user
from models import User
from database import get_db
from sqlalchemy.orm import Session
import logging

logging.basicConfig(level=logging.INFO)


def admin_only(current_user: dict, db: Session = Depends(get_db)):
    if isinstance(current_user, dict):
        user_type = current_user.get("type")
    else:
        user_type = current_user.type

    if user_type not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    return current_user

def superadmin_only(current_user: User = Depends(get_current_user)):
    if not current_user.is_superadmin:
        print(f"Unauthorized user: {current_user.user_id}, {current_user.mobile_number}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access. Only superadmins are allowed."
        )
    return current_user

