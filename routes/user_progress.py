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
from services.classes import create_response
router = APIRouter()


@router.put("/user-progress/")
def update_user_topic_progress(
    update_data: UpdateProgressRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Validate that the topic exists
        topic = db.query(Topic).filter(Topic.id == update_data.topic_id).first()
        if not topic:
            return create_response(
                success=False,
                message="Topic not found",
                data=None
            )
        
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

        return create_response(
            success=True,
            message="Progress updated successfully",
            data={
                "topic_id": update_data.topic_id,
                "is_completed": user_topic_progress.is_completed,
            }
        )
    except Exception as e:
        return create_response(
            success=False,
            message=f"An unexpected error occurred: {str(e)}",
            data=None
        )

# @router.get("/user-progress/{user_id}")
# def get_user_progress(
#     user_id: str,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     try:
#         # Validate the current user
#         if user_id != current_user.user_id:
#             return create_response(
#                 success=False,
#                 message="Unauthorized access to this user's data",
#                 data=None
#             )

#         # Get user data
#         user = db.query(User).filter(User.user_id == user_id).first()
#         if not user:
#             return create_response(
#                 success=False,
#                 message="User not found",
#                 data=None
#             )

#         # Get the user's class
#         user_class = db.query(Class).filter(Class.id == user.user_class).first()
#         if not user_class:
#             return create_response(
#                 success=True,
#                 message="No subjects found for the user",
#                 data={"user_id": user_id, "subjects": []}
#             )

#         response_subjects = []
#         for subject in user_class.subjects:
#             chapters_data = []
#             subject_has_completed_topic = False

#             for chapter in subject.chapters:
#                 topics_data = []
#                 for topic in chapter.topics:
#                     user_topic = db.query(UserTopicProgress).filter(
#                         UserTopicProgress.user_id == user_id,
#                         UserTopicProgress.topic_id == topic.id,
#                     ).first()

#                     # Determine if topic is completed
#                     is_completed = user_topic.is_completed if user_topic else False
#                     topics_data.append({
#                         "topic_id": topic.id,
#                         "is_completed": is_completed,
#                     })

#                     # Check if the topic is completed for subject inclusion
#                     if is_completed:
#                         subject_has_completed_topic = True

#                 # Include the chapter regardless of topic completion
#                 if topics_data:
#                     chapters_data.append({
#                         "chapter_id": chapter.id,
#                         "topics": topics_data,
#                         "chapter_progress": calculate_chapter_progress(chapter, user_id, db),
#                     })

#             # Include the subject only if it has at least one completed topic
#             if subject_has_completed_topic:
#                 response_subjects.append({
#                     "subject_id": subject.id,
#                     "chapters": chapters_data,
#                     "subject_progress": calculate_subject_progress(subject, user_id, db),
#                 })

#         # Wrap the final response in create_response
#         return create_response(
#             success=True,
#             message="User progress retrieved successfully",
#             data={"user_id": user_id, "subjects": response_subjects}
#         )

#     except Exception as e:
#         return create_response(
#             success=False,
#             message=f"An unexpected error occurred: {str(e)}",
#             data=None
#         )

@router.get("/user-progress/{user_id}")
def get_user_progress(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Validate the current user
        if user_id != current_user.user_id:
            return create_response(
                success=False,
                message="Unauthorized access to this user's data",
                data=None
            )

        # Get user data
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return create_response(
                success=False,
                message="User not found",
                data=None
            )

        # Get the user's class
        user_class = db.query(Class).filter(Class.id == user.user_class).first()
        if not user_class:
            return create_response(
                success=True,
                message="No subjects found for the user",
                data={"user_id": user_id, "subjects": []}
            )

        response_subjects = []
        for subject in user_class.subjects:
            chapters_data = []
            subject_has_completed_topic = False

            for chapter in subject.chapters:
                topics_data = []
                chapter_has_completed_topic = False

                for topic in chapter.topics:
                    user_topic = db.query(UserTopicProgress).filter(
                        UserTopicProgress.user_id == user_id,
                        UserTopicProgress.topic_id == topic.id,
                    ).first()

                    # Determine if topic is completed
                    is_completed = user_topic.is_completed if user_topic else False
                    topics_data.append({
                        "topic_id": topic.id,
                        "is_completed": is_completed,
                    })

                    # Mark chapter as having at least one completed topic
                    if is_completed:
                        chapter_has_completed_topic = True
                        subject_has_completed_topic = True

                # Only add chapters with at least one completed topic
                if chapter_has_completed_topic:
                    chapters_data.append({
                        "chapter_id": chapter.id,
                        "chapter_name" : chapter.name,
                        "topics": topics_data,
                        "chapter_progress": calculate_chapter_progress(chapter, user_id, db),
                    })

            # Include the subject only if it has at least one completed topic
            if subject_has_completed_topic:
                response_subjects.append({
                    "subject_id": subject.id,
                    "subject_name" : subject.name,
                    "chapters": chapters_data,
                    "subject_progress": calculate_subject_progress(subject, user_id, db),
                })

        # Wrap the final response in create_response
        return create_response(
            success=True,
            message="User progress retrieved successfully",
            data={"user_id": user_id, "subjects": response_subjects}
        )

    except Exception as e:
        return create_response(
            success=False,
            message=f"An unexpected error occurred: {str(e)}",
            data=None
        )
