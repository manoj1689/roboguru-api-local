from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import Optional
from schemas.topic import TopicCreate, TopicUpdate
from database import get_db
import services.topics
from utils.auth import get_current_user 
from utils.response import create_response
from datetime import datetime
from models.user import User
from utils.dependencies import superadmin_only

router = APIRouter()

@router.post("/create", response_model=None)
def create_topic(
    topic: TopicCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        db_topic = services.topics.create_topic(db=db, topic=topic, chapter_id=topic.chapter_id)
        response_data = {
            "id": db_topic.id,
            "name": db_topic.name,
            "chapter_id": db_topic.chapter_id,
            "details": db_topic.details,
            "tagline": db_topic.tagline,
            "image_link": db_topic.image_link,
            "subtopics": db_topic.subtopics,
            "is_completed": db_topic.is_completed
        }
        return create_response(success=True, message="Topic created successfully", data=response_data)
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {e}")

@router.get("/read_all_topic", response_model=None)
def read_all_topics(
    limit: int = Query(10, description="Number of records to retrieve"),
    name: Optional[str] = Query(None, description="Filter by class name"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),   
):
    try:
        topics = services.topics.get_all_topics(db, limit=limit, name=name)
        if not topics:
            return create_response(success=True, message="No topic found for the chapter", data=None)
        response_data = [
            {
                "id": sub.id,
                "name": sub.name,
                "chapter_id": sub.chapter_id,
                "tagline": sub.tagline,
                "details": sub.details,
                "image_link": sub.image_link,
                "subtopics": sub.subtopics,
                "is_completed": False
            }
            for sub in topics
        ]
        return create_response(success=True, message="Topic retrieved successfully", data=response_data)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {e}")

@router.get("/chapter/{chapter_id}", response_model=None)
def read_topic(
    chapter_id: str, 
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user), 
):
    try:
        db_topic = services.topics.get_topics_by_chapter(db=db, chapter_id=chapter_id)
        if not db_topic:
            return create_response(success=True, message="No topic found for the chapter", data=None)
        response_data = [
            {
                "id": sub.id,
                "name": sub.name,
                "chapter_id": sub.chapter_id,
                "tagline": sub.tagline,
                "details": sub.details,
                "image_link": sub.image_link,
                "subtopics": sub.subtopics,
                "is_completed": False
            }
            for sub in db_topic
        ]
        return create_response(success=True, message="Topics retrieved successfully", data=response_data)
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {e}")

@router.put("/{topic_id}", response_model=None)
def edit_topic(
    topic_id: str,
    updated_topic: TopicUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(superadmin_only), 
):
    try:
        db_topic = services.topics.get_topic(db=db, topic_id=topic_id)
        if not db_topic or db_topic.is_deleted:
            raise HTTPException(status_code=404, detail="Topic not found or deleted")

        # Update the topic fields
        db_topic.name = updated_topic.name
        db_topic.details = updated_topic.details
        db_topic.tagline = updated_topic.tagline
        db_topic.image_link = updated_topic.image_link
        db_topic.chapter_id = updated_topic.chapter_id
        db_topic.subtopics = updated_topic.subtopics

        # Validate chapter existence
        if not services.chapters.get_chapter(db=db, chapter_id=updated_topic.chapter_id):
            raise HTTPException(status_code=400, detail="Invalid chapter ID")
        
        db.add(db_topic)
        db.commit()
        db.refresh(db_topic)

        response_data = {
            "id": db_topic.id,
            "name": db_topic.name,
            "details": db_topic.details,
            "tagline": db_topic.tagline,
            "image_link": db_topic.image_link,
            "chapter_id": db_topic.chapter_id,
            "subtopics": db_topic.subtopics
        }
        return create_response(success=True, message="Topic updated successfully", data=response_data)
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message="An unexpected error occurred")

@router.delete("/{topic_id}", response_model=None)
def soft_delete_topic(
    topic_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(superadmin_only), 
):
    try:
        db_topic = services.topics.get_topic(db=db, topic_id=topic_id)
        if not db_topic or db_topic.is_deleted:
            raise HTTPException(status_code=404, detail="Topic not found or already deleted")

        # Perform soft delete
        db_topic.is_deleted = True
        db_topic.deleted_at = datetime.utcnow()
        db.commit()

        return create_response(success=True, message="Topic deleted successfully")
    except HTTPException as e:
        return create_response(success=False, message=e.detail)
    except Exception as e:
        return create_response(success=False, message="An unexpected error occurred")