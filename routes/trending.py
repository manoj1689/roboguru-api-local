from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Topic, Chapter, Subject, User, Class
import logging
from database import get_db
from schemas import UpdateTrendingTopicRequest
from services.dependencies import superadmin_only
from services.classes import create_response
from services.auth import get_current_user 
from core.config import settings
router = APIRouter()

@router.post("/trending_topics/update")
def update_trending_topic(
    request: UpdateTrendingTopicRequest,
    db: Session = Depends(get_db),
    # current_user: User = Depends(superadmin_only),  
    current_user: str = Depends(get_current_user),  

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

from sqlalchemy.orm import aliased
from sqlalchemy.sql import func, distinct
from sqlalchemy import desc, literal_column

@router.get("/trending_topics/by_class/{class_id}")
def get_trending_topics_by_class(
    class_id: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    try:
        # Subquery to assign row numbers per subject
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

        # Select only top 5 per subject
        trending_topics = (
            db.query(subquery)
            .filter(subquery.c.row_num <= settings.TRENDING_TOPICS_LIMIT)
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

        return create_response(
            success=True,
            message="Trending topics retrieved successfully",
            data=response_data,
        )
    except Exception as e:
        return create_response(success=False, message=f"An unexpected error occurred: {e}")


# @router.get("/trending_topics/current_user_class")
# def get_trending_topics_for_user_class(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     try:
#         # Check if the user is associated with a class
#         if not current_user.user_class:
#             logging.info("User is not associated with any class.")
#             return create_response(
#                 success=False,
#                 message="User is not associated with any class.",
#                 data=None,
#             )

#         logging.info(f"Fetching trending topics for class_id: {current_user.user_class}")

#         # Construct the query to get trending topics for the user's class
#         trending_topics_query = (
#             db.query(
#                 Topic.id,
#                 Topic.name.label("topic_name"),
#                 Topic.tagline.label("topic_tagline"),
#                 Topic.details,
#                 Topic.image_link,
#                 Topic.priority,
#                 Chapter.name.label("chapter_name"),
#                 Chapter.tagline.label("chapter_tagline"),
#                 Subject.id.label("subject_id"),
#                 Subject.name.label("subject_name"),
#                 Subject.tagline.label("subject_tagline"),
#             )
#             .join(Chapter, Chapter.id == Topic.chapter_id)
#             .join(Subject, Subject.id == Chapter.subject_id)
#             .filter(
#                 Topic.class_id == current_user.user_class,  # Ensure class_id matches
#                 Topic.is_trending == True,  # Only trending topics
#                 Topic.is_deleted == False,  # Only non-deleted topics
#             )
#             .order_by(Topic.priority.desc(), Topic.created_at.desc())
#         )

#         # Execute the query and fetch results
#         trending_topics = trending_topics_query.all()
#         logging.info(f"Trending topics query result: {trending_topics}")

#         # Check if any topics were found
#         if not trending_topics:
#             logging.info("No trending topics found.")
#             return create_response(
#                 success=True,
#                 message="No trending topics found for the user's class.",
#                 data=[],
#             )

#         # Prepare the response data
#         response_data = [
#             {
#                 "id": topic[0],
#                 "name": topic[1],
#                 "tagline": topic[2],
#                 "details": topic[3],
#                 "image_link": topic[4],
#                 "priority": topic[5],
#                 "chapter_name": topic[6],
#                 "chapter_tagline": topic[7],
#                 "subject_id": topic[8],
#                 "subject_name": topic[9],
#                 "subject_tagline": topic[10],
#             }
#             for topic in trending_topics
#         ]

#         return create_response(
#             success=True,
#             message="Trending topics retrieved successfully.",
#             data=response_data,
#         )

#     except Exception as e:
#         logging.error(f"Error fetching trending topics: {e}", exc_info=True)
#         return create_response(
#             success=False,
#             message="An error occurred while retrieving trending topics.",
#             data=None,
#         )


@router.post("/trending/mark_first_2")
def mark_first_2_topics_as_trending(db: Session = Depends(get_db)):
    try:
        # Fetch all classes
        classes = db.query(Class).filter(Class.is_deleted == False).all()
        
        updated_count = 0

        # Iterate through each class
        for _class in classes:
            subjects = _class.subjects
            
            # Iterate through each subject in the class
            for subject in subjects:
                chapters = subject.chapters
                
                # Iterate through each chapter in the subject
                for chapter in chapters:
                    topics = chapter.topics
                    
                    # Mark first 20 topics of each chapter as trending
                    for topic in topics[:2]:
                        if not topic.is_trending:  # Only update if it's not already trending
                            topic.is_trending = True
                            updated_count += 1
                            db.commit()
        
        return {"success": True, "message": f"Marked {updated_count} topics as trending."}
    
    except Exception as e:
        logging.error(f"Error marking topics as trending: {e}", exc_info=True)
        db.rollback()  # Rollback in case of error
        raise HTTPException(status_code=500, detail="An error occurred while marking topics as trending.")