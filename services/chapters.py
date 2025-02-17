from sqlalchemy.orm import Session
from models import Chapter, Subject
from schemas import ChapterCreate
from fastapi import HTTPException
from typing import List, Optional

def get_chapter(db: Session, chapter_id: int):
    return db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.is_deleted == False).first()

def get_all_chapters(db: Session, limit: int = 10, name: Optional[str] = None):
    query = db.query(Chapter).filter(Chapter.is_deleted == False)
    if name:
        query = query.filter(Chapter.name.ilike(f"%{name}%"))
    return query.limit(limit).all()

def get_chapters_by_subject(db: Session, subject_id: int):
    return db.query(Chapter).filter(Chapter.subject_id == subject_id, Chapter.is_deleted == False).all()

def create_chapter_in_db(db: Session, chapter: ChapterCreate, subject_id: int):
    if not db.query(Subject).filter(Subject.id == subject_id).exists():
        raise HTTPException(status_code=400, detail="Subject does not exist")
    
    if db.query(Chapter).filter(Chapter.name == chapter.name, Chapter.subject_id == subject_id).exists():
        raise HTTPException(status_code=400, detail="Chapter with this name already exists for the subject")
    
    db_chapter = Chapter(
        name=chapter.name,
        subject_id=subject_id,
        tagline=chapter.tagline,
        image_link=chapter.image_link
    )
    db.add(db_chapter)
    db.commit()
    db.refresh(db_chapter)
    return db_chapter