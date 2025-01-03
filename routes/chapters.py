from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import List, Optional
import schemas
from database import get_db
import services.chapters
from sqlalchemy.orm import Session
from services.auth import get_current_user
from services.classes import create_response
from models import Subject
from datetime import datetime

router = APIRouter()


@router.post("/create", response_model=None)
def create_chapter(
    chapter: schemas.ChapterCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),  
):
    try:
        created_chapter = services.chapters.create_chapter_in_db(db=db, chapter=chapter, subject_id=chapter.subject_id)

        response_data = {
            "id": created_chapter.id,
            "name": created_chapter.name,
            "subject_id":created_chapter.subject_id,
            "tagline": created_chapter.tagline,
            "image_link": created_chapter.image_link
        }
        return create_response(success=True, message="Chapter created successfully", data=response_data)
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message="An unexpected error occurred")

@router.get("/read_all_chapter", response_model=None)
def read_all_chapters(
    limit: int = Query(10, description="Number of records to retrieve"),
    name: Optional[str] = Query(None, description="Filter by class name"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user), 
):
    try:
        chapters_list = services.chapters.get_all_chapters(db, limit=limit, name=name)
        if not chapters_list:
            return create_response(success=True, message="No chapters found for the subject",data=None)        
        response_data = [
            {
                "id": sub.id,
                "name": sub.name,
                "subject_id":sub.subject_id,
                "tagline": sub.tagline,
                "image_link": sub.image_link
            }
            for sub in chapters_list
        ]

        return create_response(success=True, message="Chapters retrieved successfully", data=response_data)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {e}")

@router.get("/subject/{subject_id}", response_model=None)
async def get_chapters_by_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user), 
):
    try:
        chapters = services.chapters.get_chapters_by_subject(db, subject_id)
        if not chapters:
            return create_response(success=True, message="No chapters found for the subject",data=None)
        response_data = [
            {
                "id": sub.id,
                "name": sub.name,
                "subject_id":sub.subject_id,
                "tagline": sub.tagline,
                "image_link": sub.image_link
            }
            for sub in chapters
        ]

        return create_response(success=True, message="Subjects retrieved successfully", data=response_data)
    except Exception as e:
        return create_response(success=False, message="An unexpected error occurred")

@router.put("/{chapter_id}", response_model=None)
def update_chapter(
    chapter_id: int,
    chapter_data: schemas.ChapterUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        db_chapter = services.chapters.get_chapter(db, chapter_id)
        if not db_chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")

        # Validate subject_id if provided
        if chapter_data.subject_id:
            subject = db.query(Subject).filter(Subject.id == chapter_data.subject_id).first()
            if not subject:
                raise HTTPException(status_code=400, detail="Invalid subject_id")

        # Update chapter fields
        db_chapter.name = chapter_data.name or db_chapter.name
        db_chapter.tagline = chapter_data.tagline or db_chapter.tagline
        db_chapter.image_link = chapter_data.image_link or db_chapter.image_link
        db_chapter.subject_id = chapter_data.subject_id or db_chapter.subject_id

        db.add(db_chapter)
        db.commit()
        db.refresh(db_chapter)

        response_data = {
            "id": db_chapter.id,
            "name": db_chapter.name,
            "subject_id": db_chapter.subject_id,
            "tagline": db_chapter.tagline,
            "image_link": db_chapter.image_link,
        }
        return create_response(success=True, message="Chapter updated successfully", data=response_data)
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {e}")


@router.delete("/{chapter_id}", response_model=None)
def delete_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        db_chapter = services.chapters.get_chapter(db, chapter_id)
        if not db_chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")

        db_chapter.is_deleted = True
        db_chapter.deleted_at = datetime.utcnow()
        db.commit()

        return create_response(success=True, message="Chapter deleted successfully")
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {e}")





# @router.get("/{chapter_id}", response_model=schemas.Chapter)
# def read_chapter(chapter_id: int, db: Session = Depends(get_db)):
#     db_chapter = services.chapters.get_chapter(db=db, chapter_id=chapter_id)
#     if db_chapter is None:
#         raise HTTPException(status_code=404, detail="Chapter not found")
#     return db_chapter