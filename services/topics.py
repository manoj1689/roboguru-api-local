from sqlalchemy.orm import Session
from models import Topic, Chapter
from schemas import TopicCreate
from fastapi import HTTPException
from typing import Optional

# CRUD operations for Topic
def get_topic(db: Session, topic_id: int):
    return db.query(Topic).filter(topic_id == topic_id, Topic.is_deleted == False).first()

# Get subjects by class_id from the database
def get_topics_by_chapter(db: Session, chapter_id: int):
    return db.query(Topic).filter(Topic.chapter_id == chapter_id, Topic.is_deleted == False).all()


def get_all_topics(db: Session, limit: int = 10, name: Optional[str] = None):
    query = db.query(Topic).filter(
        Topic.is_deleted == False
    )
    
    if name:
        query = query.filter(Topic.name.ilike(f"%{name}%"))
    
    return query.limit(limit).all()


def create_topic(db: Session, topic: TopicCreate, chapter_id: int):
    db_topic = Topic(name=topic.name,  details=topic.details, chapter_id=chapter_id, tagline=topic.tagline, image_link=topic.image_link)

    # Check for duplicate class name
    existing_class = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not existing_class:
        raise HTTPException(status_code=400, detail="Chapter does not exists")  
    
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic


# def get_topics(db: Session, skip: int = 0, limit: int = 10):
#     return db.query(Topic).offset(skip).limit(limit).all()

