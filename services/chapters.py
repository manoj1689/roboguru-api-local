from sqlalchemy.orm import Session
from models import Chapter, Subject
from schemas import ChapterCreate
from sqlalchemy.orm import joinedload
from fastapi import HTTPException
from typing import List, Optional


# CRUD operations for Chapter
def get_chapter(db: Session, chapter_id: int):
    return db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.is_deleted == False).first()

def get_all_chapters(db: Session, limit: int = 10, name: Optional[str] = None):
    query = db.query(Chapter).filter(
        Chapter.is_deleted == False
    )
    if name:
        query = query.filter(Chapter.name.ilike(f"%{name}%"))
    return query.limit(limit).all()


def get_chapters_by_subject(db: Session, subject_id: int):
    return db.query(Chapter).filter(Chapter.subject_id == subject_id, Chapter.is_deleted == False).all()

def create_chapter_in_db(db: Session, chapter: ChapterCreate, subject_id: int):
    existing_class = db.query(Subject).filter(Subject.id == subject_id).first()
    if not existing_class:
        raise HTTPException(status_code=400, detail="Subject does not exists")  
        
    db_chapter = Chapter(name=chapter.name, subject_id=subject_id, tagline=chapter.tagline, image_link=chapter.image_link)
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    return db_chapter

    

# def get_chapters(db: Session, skip: int = 0, limit: int = 10):
#     return db.query(Chapter).options(joinedload(Chapter.topics)).offset(skip).limit(limit).all()


