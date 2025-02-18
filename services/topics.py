from sqlalchemy.orm import Session
from models.chapter import Chapter
from models.topic import Topic
from schemas.topic import TopicCreate
from fastapi import HTTPException
from typing import Optional

def get_topic(db: Session, topic_id: int):
    return db.query(Topic).filter(Topic.id == topic_id, Topic.is_deleted == False).first()

def get_topics_by_chapter(db: Session, chapter_id: int):
    return db.query(Topic).filter(Topic.chapter_id == chapter_id, Topic.is_deleted == False).all()

def get_all_topics(db: Session, limit: int = 10, name: Optional[str] = None):
    query = db.query(Topic).filter(Topic.is_deleted == False)
    if name:
        query = query.filter(Topic.name.ilike(f"%{name}%"))
    return query.limit(limit).all()

def create_topic(db: Session, topic: TopicCreate, chapter_id: int):
    if not db.query(Chapter).filter(Chapter.id == chapter_id).first():
        raise HTTPException(status_code=400, detail="Chapter does not exist")
    
    if db.query(Topic).filter(Topic.name == topic.name, Topic.chapter_id == chapter_id).first():
        raise HTTPException(status_code=400, detail="Topic with this name already exists in the chapter")
    
    db_topic = Topic(
        name=topic.name,
        details=topic.details,
        chapter_id=chapter_id,
        tagline=topic.tagline,
        image_link=topic.image_link,
        subtopics=topic.subtopics
    )
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic