from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import Optional
from schemas.subject import SubjectCreate, SubjectUpdate
from database import get_db
import services.subjects
from utils.auth import get_current_user 
from utils.response import create_response
from models.user import User
from models.classes import Class
from utils.dependencies import superadmin_only

router = APIRouter()

@router.post("/create", response_model=None)
def create_subject(
    subject: SubjectCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:   
        created_subject = services.subjects.create_subject(db=db, subject=subject)
        response_data = {
            "id": created_subject.id,
            "name": created_subject.name,
            "class_id": created_subject.class_id,
            "tagline": created_subject.tagline,
            "image_link": created_subject.image_link,
            "image_prompt": created_subject.image_prompt
        }
        return create_response(success=True, message="Subject created successfully", data=response_data)
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception:
        return create_response(success=False, message="An unexpected error occurred")

@router.get("/read_subjects_list", response_model=None)
def read_all_subjects(
    limit: int = Query(10, description="Number of records to retrieve"),
    name: Optional[str] = Query(None, description="Filter by class name"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        subjects_list = services.subjects.get_all_subjects(db, limit=limit, name=name)
        if not subjects_list:
            return create_response(success=True, message="No subjects found for the class", data=None)
        
        response_data = [
            {
                "id": sub.id,
                "name": sub.name,
                "class_id": sub.class_id,
                "tagline": sub.tagline,
                "image_link": sub.image_link,
                "image_prompt": sub.image_prompt
            }
            for sub in subjects_list
        ]
        return create_response(success=True, message="Subjects retrieved successfully", data=response_data)
    except Exception:
        return create_response(success=False, message="An unexpected error occurred")

@router.get("/class/{class_id}", response_model=None)
async def get_subjects_by_class(
    class_id: str, 
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),  
):
    try:
        subjects = services.subjects.get_subjects_by_class(db, class_id)
        if not subjects:
            return create_response(success=True, message="No subjects found for the class", data=None)
        
        response_data = [
            {
                "id": sub.id,
                "name": sub.name,
                "class_id": sub.class_id,
                "tagline": sub.tagline,
                "image_link": sub.image_link,
                "image_prompt": sub.image_prompt
            }
            for sub in subjects
        ]
        return create_response(success=True, message="Subjects retrieved successfully", data=response_data)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")

@router.put("/{subject_id}", response_model=None)
def update_subject(
    subject_id: str,
    subject_data: SubjectUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(superadmin_only), 
):
    try:
        db_subject = services.subjects.get_subject_by_id(db, subject_id)
        if not db_subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        # Validate class_id if provided
        if subject_data.class_id:
            existing_class = db.query(Class).filter(Class.id == subject_data.class_id).first()
            if not existing_class:
                raise HTTPException(status_code=400, detail="Invalid class_id provided")

        # Update the fields
        db_subject.name = subject_data.name or db_subject.name
        db_subject.tagline = subject_data.tagline or db_subject.tagline
        db_subject.image_link = subject_data.image_link or db_subject.image_link
        db_subject.image_prompt = subject_data.image_prompt or db_subject.image_prompt
        db_subject.class_id = subject_data.class_id or db_subject.class_id

        db.add(db_subject)
        db.commit()
        db.refresh(db_subject)

        response_data = {
            "id": db_subject.id,
            "name": db_subject.name,
            "class_id": db_subject.class_id,
            "tagline": db_subject.tagline,
            "image_link": db_subject.image_link,
            "image_prompt": db_subject.image_prompt,
        }
        return create_response(success=True, message="Subject updated successfully", data=response_data)
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")

@router.delete("/{subject_id}", response_model=None)
def delete_subject(
    subject_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(superadmin_only), 
):
    try:
        db_subject = services.subjects.get_subject_by_id(db, subject_id)
        if not db_subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        db_subject.is_deleted = True
        db.commit()

        return create_response(success=True, message="Subject deleted successfully")
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {str(e)}")










