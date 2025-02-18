from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from schemas import EducationLevelCreate, EducationLevelUpdate
from models.user import User
from models.education_level import EducationLevel
from services.level import get_all_education_levels, create_education_level, get_education_level
from utils.auth import get_current_user  
from utils.response import create_response
from datetime import datetime
from utils.dependencies import superadmin_only

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
    except Exception:
        return create_response(success=False, message="An unexpected error occurred")

@router.get("/read_list", response_model=None)
def read_levels_list(
    limit: int = Query(10, description="Number of records to retrieve"),
    name: Optional[str] = Query(None, description="Filter by education level name"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        level_list = get_all_education_levels(db, limit=limit, name=name)
        if not level_list:
            return create_response(success=True, message="Education Level not found", data=None)
        
        response_data = [
            {
                "id": l.id,
                "name": l.name,
                "description": l.description,
            }
            for l in level_list
        ]
        return create_response(success=True, message="Education Level retrieved successfully", data=response_data)
    except Exception:
        return create_response(success=False, message="An unexpected error occurred")

@router.get("/{level_id}", response_model=None)
def read_level_id(
    level_id: str,
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
    except Exception:
        return create_response(success=False, message="An unexpected error occurred")

@router.get("/levels/all_data", response_model=None)
def read_level_all_list(
    limit: int = 1000,
    name: Optional[str] = Query(None, description="Name to search for"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        levels_list = get_all_education_levels(db, limit=limit, name=name)
        if not levels_list:
            return create_response(success=False, message="Education Level not found")

        response_data = [
            {
                "id": level.id,
                "name": level.name,
                "description": level.description,
                "classes": [cls.name for cls in level.classes],
            }
            for level in levels_list
        ]
        return create_response(success=True, message="Education levels retrieved successfully", data=response_data)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")

@router.put("/{level_id}", response_model=None)
def update_level(
    level_id: str,
    level: EducationLevelUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(superadmin_only), 
):
    try:
        db_level = db.query(EducationLevel).filter(
            EducationLevel.id == level_id,
            EducationLevel.is_deleted == False
        ).first()
        if not db_level:
            raise HTTPException(status_code=404, detail="Education Level not found")

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
    except Exception:
        return create_response(success=False, message="An unexpected error occurred")

@router.delete("/{level_id}", response_model=None)
def delete_level(
    level_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(superadmin_only), 
):
    try:
        db_level = db.query(EducationLevel).filter(
            EducationLevel.id == level_id,
            EducationLevel.is_deleted == False
        ).first()
        if not db_level:
            return create_response(success=False, message="Education Level not found or already deleted")

        db_level.is_deleted = True
        db_level.deleted_at = datetime.utcnow()
        db.commit()

        return create_response(success=True, message="Education Level soft-deleted successfully")
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception:
        return create_response(success=False, message="An unexpected error occurred")