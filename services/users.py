from sqlalchemy.orm import Session
from models import User
from uuid import uuid4
from fastapi import HTTPException, status
from schemas import UserCreate
from datetime import datetime
from services.auth import create_access_token


def create_superadmin(db: Session):
    superadmin = db.query(User).filter(User.mobile_number == "9708188605").first()
    if not superadmin:
        superadmin = User(
            user_id=str(uuid4()),
            mobile_number="9708188605",
            name="Superadmin",
            is_verified=True,
            is_superadmin=True,
            type="superadmin",
            otp=1234,
        )
        db.add(superadmin)
        db.commit()
        print("Superadmin created with mobile number 9708188605.")



def get_all_users(db: Session, limit: int = 10,):
    users = db.query(User).filter(User.is_deleted == False)
    return users

def delete_user(user_id: str, db: Session):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_deleted = True
    user.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": "User deleted successfully"}
