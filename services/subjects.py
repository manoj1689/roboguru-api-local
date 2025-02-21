from sqlalchemy.orm import Session
from models.classes import Class
from models.subject import Subject
from schemas.subject import SubjectCreate
from fastapi import HTTPException
from typing import Optional

# CRUD operations for Chapter
def get_subject_by_id(db: Session, subject_id: int):
    return db.query(Subject).filter(Subject.id == subject_id, Subject.is_deleted == False).first()

# Get subjects by class_id from the database
def get_subjects_by_class(db: Session, class_id: int):
    return db.query(Subject).filter(Subject.class_id == class_id, Subject.is_deleted == False).all()

# Get all subjects from the database
def get_all_subjects(db: Session, limit: int = 10, name: Optional[str] = None):
    query = db.query(Subject).filter(Subject.is_deleted == False)
    if name:
        query = query.filter(Subject.name.ilike(f"%{name}%"))
    return query.limit(limit).all()

def create_subject(db: Session, subject: SubjectCreate):
    existing_class = db.query(Class).filter(Class.id == subject.class_id).first()
    if not existing_class:
        raise HTTPException(status_code=400, detail="Class does not exist")

    existing_subject = db.query(Subject).filter(
        Subject.name == subject.name,
        Subject.class_id == subject.class_id
    ).first()
    if existing_subject:
        raise HTTPException(status_code=400, detail="Subject with this name already exists in the class")

    # Create the new subject
    db_subject = Subject(
        name=subject.name,
        class_id=subject.class_id,
        tagline=subject.tagline,
        image_link=subject.image_link,
        image_prompt=subject.image_prompt
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject