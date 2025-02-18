from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.classes import Class
from models.subject import Subject
from models.chapter import Chapter
from models.topic import Topic
import logging
from database import get_db
from schemas.trnding_topic import UpdateTrendingTopicRequest
from utils.response import create_response
from utils.auth import get_current_user 
from core.config import settings
from sqlalchemy.sql import func, desc


router = APIRouter()

@router.post("/trending_topics/update")
def update_trending_topic(
    request: UpdateTrendingTopicRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        topic = db.query(Topic).filter(Topic.id == request.topic_id).first()
        if not topic:
            return create_response(success=True, message="Topic not found", data=None)
        
        topic.is_trending = request.is_trending
        topic.priority = request.priority
        db.commit()
        db.refresh(topic)

        response_data = {
            "topic_id": topic.id,
            "is_trending": topic.is_trending,
            "priority": topic.priority,
        }
        return create_response(success=True, message="Trending status updated successfully", data=response_data)
    except Exception as e:
        logging.error(f"Error updating trending topic: {e}", exc_info=True)
        return create_response(success=False, message="An unexpected error occurred")

@router.get("/trending_topics/by_class/{class_id}")
def get_trending_topics_by_class(
    class_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        subquery = (
            db.query(
                Topic.id,
                Topic.tagline.label("topic_tagline"),
                Topic.is_trending,
                Topic.chapter_id,
                Topic.details,
                Topic.name.label("topic_name"),
                Topic.image_link,
                Topic.priority,
                Subject.class_id,
                Subject.id.label("subject_id"),
                Subject.name.label("subject_name"),
                Subject.tagline.label("subject_tagline"),
                Chapter.name.label("chapter_name"),
                Chapter.tagline.label("chapter_tagline"),
                Topic.created_at,
                func.row_number()
                .over(
                    partition_by=Subject.id,
                    order_by=[desc(Topic.priority), desc(Topic.created_at)]
                )
                .label("row_num"),
            )
            .join(Chapter, Chapter.id == Topic.chapter_id)
            .join(Subject, Subject.id == Chapter.subject_id)
            .filter(
                Subject.class_id == class_id,
                Topic.is_trending == True
            )
            .subquery()
        )

        trending_topics = (
            db.query(subquery)
            .filter(subquery.c.row_num <= settings.TRENDING_TOPICS_LIMIT)
            .all()
        )

        if not trending_topics:
            return create_response(success=True, message="No trending topics found for the provided class_id", data=None)

        response_data = [
            {
                "id": topic.id,
                "name": topic.topic_name,
                "tagline": topic.topic_tagline,
                "details": topic.details,
                "image_link": topic.image_link,
                "priority": topic.priority,
                "chapter_id": topic.chapter_id,
                "chapter_name": topic.chapter_name,
                "chapter_tagline": topic.chapter_tagline,
                "subject_id": topic.subject_id,
                "subject_name": topic.subject_name,
                "subject_tagline": topic.subject_tagline,
            }
            for topic in trending_topics
        ]

        return create_response(success=True, message="Trending topics retrieved successfully", data=response_data)
    except Exception as e:
        logging.error(f"Error retrieving trending topics: {e}", exc_info=True)
        return create_response(success=False, message="An unexpected error occurred")

@router.post("/trending/mark_first_2")
def mark_first_2_topics_as_trending(db: Session = Depends(get_db)):
    try:
        classes = db.query(Class).filter(Class.is_deleted == False).all()
        updated_count = 0

        for _class in classes:
            for subject in _class.subjects:
                for chapter in subject.chapters:
                    for topic in chapter.topics[:2]:
                        if not topic.is_trending:
                            topic.is_trending = True
                            updated_count += 1
                            db.commit()
        
        return {"success": True, "message": f"Marked {updated_count} topics as trending."}
    except Exception as e:
        logging.error(f"Error marking topics as trending: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while marking topics as trending.")