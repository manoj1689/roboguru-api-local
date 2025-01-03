from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import List,Optional
from database import get_db
from schemas import EducationLevelCreate, ReadEducationLevelRequest, EducationLevelUpdate
from models import EducationLevel
from services.level import get_all_education_levels, create_education_level, get_all_education_levels, get_education_level
from services.auth import get_current_user  
from services.classes import create_response
from datetime import datetime


router = APIRouter()

@router.post("/create/", response_model=None)
def create_level(
    level: EducationLevelCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        created_level = create_education_level(db=db, level=level)
        response_data = {
            "id": created_level.id,
            "name": created_level.name,
            "description": created_level.description
        }
        return create_response(success=True, message="Education Level created successfully", data=response_data)
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message="An unexpected error occurred")
       

@router.get("/read_list", response_model=None)
def read_levels_list(
    limit: int = Query(10, description="Number of records to retrieve"),
    name: Optional[str] = Query(None, description="Filter by education level name"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        # Fetch education levels from the database
        level_list = get_all_education_levels(db, limit=limit, name=name)
        
        # If table exists but has no entries, return null for data
        if not level_list:
            return create_response(success=True, message="Education Level not found", data=None)
        
        # Prepare response data if records exist
        response_data = [
            {
                "id": l.id,
                "name": l.name,
                "description": l.description,
            }
            for l in level_list
        ]

        return create_response(success=True, message="Education Level retrieved successfully", data=response_data)
    except Exception as e:
        # Handle unexpected errors
        return create_response(success=False, message="An unexpected error occurred")


@router.get("/{level_id}", response_model=None)
def read_level_id(
    level_id: int = 1000,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),  
):
    try:
        db_level = get_education_level(db=db, level_id=level_id)
        if db_level is None:
            return create_response(success=False, message="Education Level not found")

        response_data = {
            "id": db_level.id,
            "name": db_level.name,
            "description": db_level.description
        }

        return create_response(success=True, message="Education levels retrieved successfully", data=response_data)
    except Exception as e:
        return create_response(success=False, message="An unexpected error occurred")

@router.get("/levels/all_data", response_model=None)
def read_level_all_list(
    limit: int = 1000,
    name: str = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user), 
):
    try:
        levels_list = get_all_education_levels(db, limit=limit, name=name)
        if levels_list is None:
            return create_response(success=False, message="Education Level not found")
        response_data = [
            {
                "id": l.id,
                "name": l.name,
                "description": l.description,
                "classes": [c.name for c in l.classes]
            }
            for l in levels_list
        ]

        return create_response(success=True, message="Education levels retrieved successfully", data=response_data)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")
    
@router.put("/{level_id}", response_model=None)
def update_level(
    level_id: int,
    level: EducationLevelUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        db_level = db.query(EducationLevel).filter(
            EducationLevel.id == level_id,
            EducationLevel.is_deleted == False
        ).first()
        if not db_level:
            raise HTTPException(status_code=404, detail="Education Level not found")

        # Update fields dynamically
        for key, value in level.dict(exclude_unset=True).items():
            setattr(db_level, key, value)

        db.commit()
        db.refresh(db_level)

        response_data = {
            "id": db_level.id,
            "name": db_level.name,
            "description": db_level.description
        }
        return create_response(success=True, message="Education Level updated successfully", data=response_data)
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message="An unexpected error occurred")


@router.delete("/{level_id}", response_model=None)
def delete_level(
    level_id: int,
    # delete_request: EducationLevelDeleteRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        db_level = db.query(EducationLevel).filter(
            EducationLevel.id == level_id,
            EducationLevel.is_deleted == False
        ).first()
        if not db_level:
            return create_response(success=False, message="Education Level not found or already deleted")

        # Perform soft delete
        db_level.is_deleted = True
        db_level.deleted_at = datetime.utcnow()
        db.commit()

        return create_response(success=True, message="Education Level soft-deleted successfully")
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message="An unexpected error occurred")