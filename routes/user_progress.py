from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Topic, Class, UserTopicProgress, User
import logging
from database import get_db
from schemas import UserProgressResponse, UpdateProgressRequest, SubjectResponse, TopicResponse, ChapterResponse
from services.dependencies import superadmin_only 
from services.user_progress import calculate_chapter_progress, calculate_subject_progress
from services.auth import get_current_user 
from datetime import datetime

router = APIRouter()


# @router.get("/user-progress/{user_id}", response_model=UserProgressResponse)
# def get_user_progress(
#     user_id: str,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     # Use authenticated user or validate `user_id`
#     if user_id != current_user.user_id:
#         raise HTTPException(status_code=403, detail="Unauthorized access to this user's data")

#     # Check if user exists
#     user = db.query(User).filter(User.user_id == current_user.user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Check if user's class exists
#     user_class = db.query(Class).filter(Class.id == user.user_class).first()
#     if not user_class:
#         return {
#             "success": True,
#             "message": "User has no associated class",
#             "data": {"user_id": user_id, "subjects": []},
#         }

#     response_subjects = []
#     for subject in user_class.subjects:
#         chapters_data = []
#         for chapter in subject.chapters:
#             chapter_progress = calculate_chapter_progress(chapter, user_id, db)
#             topics_data = []
#             for topic in chapter.topics:
#                 user_topic = db.query(UserTopicProgress).filter(
#                     UserTopicProgress.user_id == user_id,
#                     UserTopicProgress.topic_id == topic.id,
#                 ).first()

#                 topics_data.append(TopicResponse(
#                     topic_id=topic.id,
#                     topic_name=topic.name,
#                     is_completed=user_topic.is_completed if user_topic else False,
#                 ))

#             chapters_data.append(ChapterResponse(
#                 chapter_id=chapter.id,
#                 chapter_name=chapter.name,
#                 topics=topics_data,
#                 chapter_progress=chapter_progress,
#             ))

#         subject_progress = calculate_subject_progress(subject, user_id, db)
#         response_subjects.append(SubjectResponse(
#             subject_id=subject.id,
#             subject_name=subject.name,
#             chapters=chapters_data,
#             subject_progress=subject_progress,
#         ))

#     return {
#         "success": True,
#         "message": "User progress retrieved successfully",
#         "data": UserProgressResponse(user_id=user_id, subjects=response_subjects),
#     }


# @router.put("/user-progress/")
# def update_user_topic_progress(
#     update_data: UpdateProgressRequest,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     # Check if topic exists and the user has the right to update it
#     topic = db.query(Topic).filter(Topic.id == update_data.topic_id).first()
#     if not topic:
#         raise HTTPException(status_code=404, detail="Topic not found")

#     # Check if user-topic-progress exists
#     user_topic_progress = db.query(UserTopicProgress).filter(
#         UserTopicProgress.user_id == current_user.user_id,
#         UserTopicProgress.topic_id == update_data.topic_id,
#     ).first()

#     if not user_topic_progress:
#         # Verify topic existence before creating progress record
#         topic = db.query(Topic).filter(Topic.id == update_data.topic_id).first()
#         if not topic:
#             raise HTTPException(status_code=404, detail="Topic not found")

#         # Create new progress record
#         user_topic_progress = UserTopicProgress(
#             user_id=current_user.user_id,
#             topic_id=update_data.topic_id,
#             is_completed=update_data.is_completed,
#         )
#         db.add(user_topic_progress)
#     else:
#         # Update existing record
#         user_topic_progress.is_completed = update_data.is_completed

#     user_topic_progress.last_updated = datetime.utcnow()
#     db.commit()
#     db.refresh(user_topic_progress)

#     return {
#         "message": "Progress updated successfully",
#         "topic_id": update_data.topic_id,
#         "is_completed": user_topic_progress.is_completed,
#     }

@router.put("/user-progress/")
def update_user_topic_progress(
    update_data: UpdateProgressRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ensure topic_id is valid and update progress
    if not update_data.topic_id:
        raise HTTPException(status_code=400, detail="Topic ID is required")

    # Validate that the topic exists
    topic = db.query(Topic).filter(Topic.id == update_data.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Check if the user has progress for this topic
    user_topic_progress = db.query(UserTopicProgress).filter(
        UserTopicProgress.user_id == current_user.user_id,
        UserTopicProgress.topic_id == update_data.topic_id,
    ).first()

    if not user_topic_progress:
        # Create new progress record if none exists
        user_topic_progress = UserTopicProgress(
            user_id=current_user.user_id,
            topic_id=update_data.topic_id,
            is_completed=update_data.is_completed,
            last_updated=datetime.utcnow(),
        )
        db.add(user_topic_progress)
    else:
        # Update existing record
        user_topic_progress.is_completed = update_data.is_completed
        user_topic_progress.last_updated = datetime.utcnow()

    db.commit()
    db.refresh(user_topic_progress)

    return {
        "message": "Progress updated successfully",
        "topic_id": update_data.topic_id,
        "is_completed": user_topic_progress.is_completed,
    }
@router.get("/user-progress/{user_id}", response_model=UserProgressResponse)
def get_user_progress(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check that the requested user is the authenticated user
    if user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this user's data")

    # Fetch the user from the database
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch the user's class, if exists
    user_class = db.query(Class).filter(Class.id == user.user_class).first()
    if not user_class:
        raise HTTPException(status_code=404, detail="User is not assigned to a class")

    # Prepare subjects with chapters and topics
    response_subjects = []
    for subject in user_class.subjects:
        chapters_data = []
        for chapter in subject.chapters:
            chapter_progress = calculate_chapter_progress(chapter, user_id, db)
            topics_data = []
            for topic in chapter.topics:
                user_topic = db.query(UserTopicProgress).filter(
                    UserTopicProgress.user_id == user_id,
                    UserTopicProgress.topic_id == topic.id,
                ).first()

                topics_data.append(TopicResponse(
                    topic_id=topic.id,
                    topic_name=topic.name,
                    is_completed=user_topic.is_completed if user_topic else False,
                    tagline=topic.tagline or "",
                    image_link=topic.image_link or "",
                    details=topic.details or "",
                ))

            chapters_data.append(ChapterResponse(
                chapter_id=chapter.id,
                chapter_name=chapter.name,
                topics=topics_data,
                chapter_progress=chapter_progress,
                tagline=chapter.tagline or "",
                image_link=chapter.image_link or "",
            ))

        subject_progress = calculate_subject_progress(subject, user_id, db)
        response_subjects.append(SubjectResponse(
            subject_id=subject.id,
            subject_name=subject.name,
            chapters=chapters_data,
            subject_progress=subject_progress,
            tagline=subject.tagline or "",
            image_link=subject.image_link or "",
            image_prompt=subject.image_prompt or "",
        ))

    return UserProgressResponse(
        user_id=user_id,
        subjects=response_subjects if response_subjects else None,
    )

