from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from utils.auth import create_access_token, create_refresh_token
from database import get_db
from models.user import User
from utils.dependencies import superadmin_only
from uuid import uuid4
from utils.response import create_response
from schemas.user import OTPRequest, OTPVerification, AdminLogin
from jose import JWTError, jwt
from core.config import settings

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/signin")
def send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.mobile_number == request.mobile_number).first()
    
    if not user:
        user = User(mobile_number=request.mobile_number, otp=None, is_verified=False)
        db.add(user)
        db.commit()

    otp = "1234"  
    user.otp = otp
    db.commit()
    print(f"OTP for {request.mobile_number}: {otp}") 

    return {"message": "OTP sent successfully"}



@router.post("/verify_otp")
def verify_otp(request: OTPVerification, db: Session = Depends(get_db)):
    try:
        # Check if the user exists based on mobile_number (user_id here refers to the mobile number)
        user = db.query(User).filter(User.mobile_number == request.user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found. Please register first."
            )

        # Verify OTP
        if user.otp != request.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP. Please try again."
            )

        user.is_verified = True
        user.otp = None  
        db.commit()

        # Generate access token using user.user_id (not mobile number)
        access_token = create_access_token(data={"sub": user.user_id, "role": user.type})
        refresh_token = create_refresh_token(data={"sub": user.mobile_number})
        
        return create_response(
            success=True,
            message="Verification successful. Login successful.",
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "role": user.type
            }
        )
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(
            success=False,
            message=f"An error occurred: {str(e)}"
        )


@router.post("/admin/login")
def login(request: AdminLogin, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.mobile_number == request.mobile_number).first()
        
        if not user or not user.is_superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized access. Only superadmins are allowed."
            )
        
        otp = "1234"  
        user.otp = otp
        db.commit() 

        if user.otp != otp:  
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP."
            )
        user.is_verified = True
        user.otp = None
        db.commit()

        access_token = create_access_token(data={"sub": user.mobile_number, "role": "superadmin"})
        refresh_token = create_refresh_token(data={"sub": user.mobile_number})
        return create_response(
            success=True,
            message="Login successful.",
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                  "token_type": "bearer",
                    "role": user.type
            }
        )
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(
            success=False,
            message=f"An error occurred: {str(e)}"
        )

@router.get("/admin/profile")
def view_profile(
    db: Session = Depends(get_db), 
    current_user: User = Depends(superadmin_only)
    
):
    return create_response(
        success=True,
        message="Admin profile retrieved successfully.",
        data={
        "name": current_user.name,
        "mobile_number": current_user.mobile_number
        }
    )










# @router.post("/verify_otp")
# def verify_otp(mobile_number: str, otp: str, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.mobile_number == mobile_number).first()
    
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

#     if user.otp != otp:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")


#     user.is_verified = True
#     user.otp = None  
#     db.commit()

#     access_token = create_access_token(data={"sub": user.user_id})

#     return {"message": "Login successful", "access_token": access_token}
