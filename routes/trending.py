from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Topic, Chapter, Subject, User
import logging
from database import get_db
from schemas import UpdateTrendingTopicRequest
from services.dependencies import superadmin_only
from services.classes import create_response
router = APIRouter()

@router.post("/trending_topics/update")
def update_trending_topic(
    request: UpdateTrendingTopicRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(superadmin_only),     
):
    try:
        topic = db.query(Topic).filter(Topic.id == request.topic_id).first()
        if not topic:
            return create_response(
                    success=True,
                    message="Topic not found",
                    data=None,
                )
        topic.is_trending = request.is_trending
        topic.priority = request.priority
        db.commit()
        db.refresh(topic)

        response_data = {
            "topic_id": topic.id,
            "is_trending": topic.is_trending,
            "priority": topic.priority,
        }
        return create_response(
            success=True,
            message="Trending status updated successfully",
            data=response_data,
        )
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {e}")

@router.get("/trending_topics/by_class/{class_id}")
def get_trending_topics_by_class(
    class_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(superadmin_only), 
):
    try:
        trending_topics = (
            db.query(
                Topic.id,
                Topic.tagline.label("topic_tagline"),
                Topic.is_trending,
                Topic.chapter_id,
                Topic.is_deleted,
                Topic.updated_at,
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
                Topic.deleted_at,
            )
            .join(Chapter, Chapter.id == Topic.chapter_id)
            .join(Subject, Subject.id == Chapter.subject_id)
            .filter(
                Subject.class_id == class_id,
                Topic.is_trending == True
            )
            .order_by(Topic.priority.desc(), Topic.created_at.desc())
            .all()
        )

        if not trending_topics:
            return create_response(
                success=True,
                message="No trending topics found for the provided class_id",
                data=None,
            )

        response_data = [
            {
                "id": topic[0],
                "name": topic[7],
                "tagline": topic[1],
                "details": topic[6],
                "image_link": topic[8],
                "priority": topic[9],
                "chapter_id": topic[3],
                "chapter_name": topic[14],
                "chapter_tagline": topic[15],
                "subject_id": topic[11],
                "subject_name": topic[12],
                "subject_tagline": topic[13],
            }
            for topic in trending_topics
        ]

        return create_response(
            success=True,
            message="Trending topics retrieved successfully",
            data=response_data,
        )
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {e}")
