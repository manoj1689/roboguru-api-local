from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, EducationLevel, Class
from services.users import (
    get_all_users,
    delete_user,
)
from services.auth import create_access_token
from services.dependencies import superadmin_only  
from schemas import OTPRequest, UserProfileResponse, UpdateUserProfileRequest
from services.auth import get_current_user  
from services.classes import create_response


router = APIRouter()

@router.post("/register")
def register(request: OTPRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.mobile_number == request.mobile_number).first()

        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already registered. Please sign in."
            )
        
        otp = "1234"
        new_user = User(
            mobile_number=request.mobile_number,
            otp=otp,
            is_verified=True, 
            type="normal" 
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        access_token = create_access_token(data={"sub": new_user.mobile_number})
        print(f"OTP for {request.mobile_number}: {otp}")

        return create_response(
            success=True,
            message="Registration successful.",
            data={
                "mobile_number": new_user.mobile_number,
                "access_token": access_token,
                "token_type": "bearer",
                "role": new_user.type
            }
        )
    except Exception as e:
        return create_response(
            success=False,
            message=f"An error occurred: {str(e)}"
        )

@router.get("/users", response_model=None)
def list_all_users(
    limit: int = Query(10, description="Number of records to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    superadmin_only(current_user, db)

    try:
        user_list = get_all_users(db=db, limit=limit)
        if not user_list:
            return create_response(success=False, message="No users found")
        response_data = [
            {
                "id": user.user_id,
                "name": user.name,
                "mobile_number": user.mobile_number,
                "email": user.email,
                "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
                "occupation": user.occupation,
            }
            for user in user_list
        ]

        return create_response(success=True, message="User list retrieved successfully", data=response_data)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")


@router.get("/profile", response_model=UserProfileResponse)
def get_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Validated user
):
    try:
        # Fetch user details from the database
        user = db.query(User).filter(User.mobile_number == current_user.mobile_number).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Prepare the profile response
        profile_data = {
            "id": user.user_id,
            "name": user.name,
            "mobile_number": user.mobile_number,
            "email": user.email,
            "date_of_birth": user.date_of_birth,
            "occupation": user.occupation,
            "is_verified": user.is_verified,
            "education_level": user.education_level,
            "user_class": user.user_class,
            "language": user.language,
        }

        return create_response(
            success=True,
            message="User profile retrieved successfully",
            data=profile_data
        )
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        print(f"Error while fetching user profile: {e}")  # Log the full error
        return create_response(
            success=False,
            message="An unexpected error occurred. Please try again later.",
            data={}
        )

@router.put("/profile/update", response_model=None)
def update_user_profile(
    profile_data: UpdateUserProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Fetch the user from the database
        user = db.query(User).filter(User.user_id == current_user.user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Convert profile_data to a dictionary
        profile_data_dict = profile_data.dict(exclude_unset=True)

        # Handle foreign key fields
        if "education_level" in profile_data_dict:
            education_level = (
                db.query(EducationLevel)
                .filter(EducationLevel.name == profile_data_dict["education_level"])
                .first()
            )
            if not education_level:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid education level"
                )
            profile_data_dict["education_level"] = education_level.id

        if "user_class" in profile_data_dict:
            user_class = (
                db.query(Class)
                .filter(Class.name == profile_data_dict["user_class"])
                .first()
            )
            if not user_class:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user class"
                )
            profile_data_dict["user_class"] = user_class.id

        # Update user details based on provided data
        allowed_fields = [
            "name", "email", "date_of_birth", "occupation",
            "education_level", "user_class", "language", "profile_image"
        ]
        for field in allowed_fields:
            if field in profile_data_dict:
                setattr(user, field, profile_data_dict[field])

        # Save changes to the database
        db.commit()
        db.refresh(user)

        # Format response data
        response_data = {
            "id": user.user_id,
            "name": user.name,
            "mobile_number": user.mobile_number,
            "email": user.email,
            "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
            "occupation": user.occupation,
            "education_level": user.education_level,
            "user_class": user.user_class,
            "language": user.language,
            "profile_image": user.profile_image,
        }

        return create_response(
            success=True,
            message="User profile updated successfully",
            data=response_data
        )
    except Exception as e:
        return create_response(
            success=False,
            message=f"An unexpected error occurred: {str(e)}"
        )



@router.delete("/users/{user_id}")
def remove_user(user_id: str, db: Session = Depends(get_db), _: User = Depends(superadmin_only)):
    return delete_user(user_id, db)
