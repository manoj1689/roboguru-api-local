from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Topic, Chapter, Subject, Class
import logging
from database import get_db
from schemas import UpdateTrendingTopicRequest
from services.dependencies import superadmin_only
router = APIRouter()


@router.get("/trending_topics/all_trending_topics/")
def get_trending_topics(db: Session = Depends(get_db)):
    trending_topics = (
        db.query(Topic)
        .filter(Topic.is_trending == True)
        .order_by(Topic.priority.desc(), Topic.created_at.desc())
        .all()
    )
    return trending_topics


@router.post("/trending_topics/update")
def update_trending_topic(
    request: UpdateTrendingTopicRequest,
    db: Session = Depends(get_db),
):
    # Fetch the topic by ID
    topic = db.query(Topic).filter(Topic.id == request.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Update the topic fields
    topic.is_trending = request.is_trending
    topic.priority = request.priority
    db.commit()
    db.refresh(topic)

    return {"message": "Trending status updated successfully", "topic": topic}












# @router.get("/trending_topics/{class_id}")
# def get_trending_topics(
#     class_id: int,  
#     db: Session = Depends(get_db)
# ):
#     logging.info(f"Fetching trending topics for class ID: {class_id}")
    
#     try:
#         query = (
#             db.query(Topic)
#             .join(Chapter, Chapter.id == Topic.chapter_id)  
#             .join(Subject, Subject.id == Chapter.subject_id)  
#             .join(Class, Class.id == Subject.class_id) 
#             .filter(Class.id == class_id) 
#             .filter(Topic.is_trending == True)  
#             .order_by(Topic.priority.desc(), Topic.created_at.desc()) 
#         )

#         trending_topics = query.all()

#         if not trending_topics:
#             logging.warning(f"No trending topics found for class ID: {class_id}")
#             raise HTTPException(status_code=404, detail=f"No trending topics found for class ID {class_id}")

#         logging.info(f"Found {len(trending_topics)} trending topics for class ID: {class_id}")
        
#         return trending_topics

#     except Exception as e:
#         logging.error(f"Error while fetching trending topics for class ID: {class_id} - {str(e)}")
#         raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching trending topics.")


# @router.get("/trending_topics/{class_id}")
# def get_trending_topics(
#     class_id: int,
#     page: int = 1,  # Add pagination
#     limit: int = 10,  # Set a default limit for results
#     db: Session = Depends(get_db),
#     _ = Depends(superadmin_only)  # Ensure only superadmins can access this route
# ):
#     logging.info(f"Fetching trending topics for class ID: {class_id}")
    
#     try:
#         query = (
#             db.query(Topic)
#             .join(Chapter, Chapter.id == Topic.chapter_id)  
#             .join(Subject, Subject.id == Chapter.subject_id)  
#             .join(Class, Class.id == Subject.class_id) 
#             .filter(Class.id == class_id) 
#             .filter(Topic.is_trending == True)  
#             .order_by(Topic.priority.desc(), Topic.created_at.desc()) 
#         )

#         # Pagination
#         trending_topics = query.offset((page - 1) * limit).limit(limit).all()

#         if not trending_topics:
#             logging.warning(f"No trending topics found for class ID: {class_id}")
#             raise HTTPException(status_code=404, detail=f"No trending topics found for class ID {class_id}")

#         logging.info(f"Found {len(trending_topics)} trending topics for class ID: {class_id}")
        
#         return trending_topics

#     except Exception as e:
#         logging.error(f"Error while fetching trending topics for class ID: {class_id} - {str(e)}")
#         raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching trending topics.")

# @router.get("/trending_topics/all_trending_topics/")
# def get_trending_topics(db: Session = Depends(get_db), _ = Depends(superadmin_only)): 
#     trending_topics = (
#         db.query(Topic)
#         .filter(Topic.is_trending == True)
#         .order_by(Topic.priority.desc(), Topic.created_at.desc())
#         .all()
#     )
#     return trending_topics

# @router.post("/trending_topics/update")
# def update_trending_topic(
#     request: UpdateTrendingTopicRequest,
#     db: Session = Depends(get_db),
#     _ = Depends(superadmin_only) 
# ):
#     # Fetch the topic by ID
#     topic = db.query(Topic).filter(Topic.id == request.topic_id).first()
#     if not topic:
#         raise HTTPException(status_code=404, detail="Topic not found")

#     # Validate priority and trending status
#     if not isinstance(request.priority, int) or request.priority < 0:
#         raise HTTPException(status_code=400, detail="Priority must be a non-negative integer.")
    
#     if not isinstance(request.is_trending, bool):
#         raise HTTPException(status_code=400, detail="is_trending must be a boolean value.")
    
#     # Update the topic fields
#     topic.is_trending = request.is_trending
#     topic.priority = request.priority
#     try:
#         db.commit()
#         db.refresh(topic)
#         return {"message": "Trending status updated successfully", "topic": topic}
#     except Exception as e:
#         logging.error(f"Error updating topic {request.topic_id}: {str(e)}")
#         db.rollback()
#         raise HTTPException(status_code=500, detail="An error occurred while updating the topic.")

