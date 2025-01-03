from fastapi import Body, APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import schemas
from database import get_db
from services.classes import get_class_by_level ,create_class_in_db, get_all_classes, get_class, create_response
from services.auth import get_current_user  
from models import EducationLevel, Class
from datetime import datetime

router = APIRouter()

@router.post("/create/", response_model=None)
def create_class(
    classes: schemas.ClassCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user), 
):
    try:
        created_class = create_class_in_db(db=db, classes=classes)
        response_data = {
            "id": created_class.id,
            "name": created_class.name,
            "level_id": created_class.level_id,#forgien key
            "tagline": created_class.tagline,
            "image_link": created_class.image_link
        }
        return create_response(success=True, message="Class created successfully", data=response_data)
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message="An unexpected error occurred")
    
@router.get("/read_class_list", response_model=None)
def read_classes(
    limit: int = Query(10, description="Number of records to retrieve"),
    name: Optional[str] = Query(None, description="Filter by class name"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        # Fetch the classes from the database
        classes_list = get_all_classes(db, limit=limit, name=name)

        # If the table exists but has no entries, return null for data
        if not classes_list:
            return create_response(
                success=True,
                message="No class data found",
                data=None
            )

        # Prepare the response data if records exist
        response_data = [
            {
                "id": cls.id,
                "name": cls.name,
                "level_id": cls.level_id,
                "tagline": cls.tagline,
                "image_link": cls.image_link,
                "subjects": [subject.name for subject in cls.subjects],
            }
            for cls in classes_list
        ]

        return create_response(
            success=True,
            message="Classes retrieved successfully",
            data=response_data
        )
    except Exception as e:
        # Handle unexpected errors
        print(f"Error retrieving classes: {e}")
        return create_response(
            success=False,
            message="An unexpected error occurred",
            data=None
        )


@router.get("/read_all_data/", response_model=None)
def read_all_classes(
    limit: int = Query(1000, description="Number of records to retrieve"),
    name: Optional[str] = Query(None, description="Filter by class name"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),   
):
    try:
        classes_list = get_all_classes(db, limit=limit, name=name)
        if not classes_list:
            return create_response(success=False, message="No classes found for this level")
        response_data = [
            {
                "id": cls.id,
                "name": cls.name,
                "level_id": cls.level_id,
                "tagline": cls.tagline,
                "image_link": cls.image_link
            }
            for cls in classes_list
        ]

        return create_response(success=True, message="Classes retrieved successfully", data=response_data)
    except Exception as e:
        return create_response(success=False, message="An unexpected error occurred")


@router.get("/level/{level_id}", response_model=None)
def read_class(
    level_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        db_classes = get_class_by_level(db=db, level_id=level_id)
        if not db_classes:
            return create_response(success=False, message="No classes found for this level")

        response_data = [
            {
                "id": cls.id,
                "name": cls.name,
                "level_id": cls.level_id,
                "tagline": cls.tagline,
                "image_link": cls.image_link
            }
            for cls in db_classes
        ]

        return create_response(success=True, message="Classes retrieved successfully", data=response_data)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")

@router.put("/{class_id}", response_model=None)
def update_class(
    class_id: int,
    class_data: schemas.ClassUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        # Fetch class by ID
        db_class = db.query(Class).filter(Class.id == class_id, Class.is_deleted == False).first()
        if not db_class:
            return create_response(success=False, message="Class not found")
        
        # Validate level_id if provided
        if class_data.level_id:
            level_exists = db.query(EducationLevel).filter(
                EducationLevel.id == class_data.level_id,
                EducationLevel.is_deleted == False
            ).first()
            if not level_exists:
                raise HTTPException(status_code=400, detail="Invalid level_id provided")

        if class_data.name:
            db_class.name = class_data.name
        if class_data.tagline:
            db_class.tagline = class_data.tagline
        if class_data.image_link:
            db_class.image_link = class_data.image_link
        if class_data.level_id:
            db_class.level_id = class_data.level_id

        db.add(db_class)
        db.commit()
        db.refresh(db_class)

        response_data = {
            "id": db_class.id,
            "name": db_class.name,
            "level_id": db_class.level_id,
            "tagline": db_class.tagline,
            "image_link": db_class.image_link,
        }
        return create_response(success=True, message="Class updated successfully", data=response_data)
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")

@router.delete("/{class_id}", response_model=None)
def delete_class(
    class_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        # Fetch class by ID
        db_class = db.query(Class).filter(Class.id == class_id, Class.is_deleted == False).first()
        if not db_class:
            raise HTTPException(status_code=404, detail="Class not found")

        # Soft delete
        db_class.is_deleted = True
        db_class.deleted_at = datetime.utcnow()

        db.add(db_class)
        db.commit()

        return create_response(success=True, message="Class deleted successfully")
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")
