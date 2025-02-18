from sqlalchemy.orm import Session
from models.education_level import EducationLevel
from models.classes import Class
from schemas.classes import ClassCreate
from fastapi import HTTPException
from typing import Optional

def get_class(db: Session, class_id: int):
    return db.query(Class).filter(Class.id == class_id).first()

def get_all_classes(db: Session, limit: int = 10, name: Optional[str] = None):
    query = db.query(Class).filter(Class.is_deleted == False)
    if name:
        query = query.filter(Class.name.ilike(f"%{name}%"))
    return query.limit(limit).all()

def create_class_in_db(db: Session, classes: ClassCreate):
    if db.query(Class).filter(Class.name == classes.name).first():
        raise HTTPException(status_code=400, detail="A class with this name already exists")
    
    level = db.query(EducationLevel).filter(EducationLevel.id == classes.level_id).first()
    if not level:
        raise HTTPException(status_code=404, detail="Education level does not exist")
    
    db_class = Class(
        name=classes.name, 
        tagline=classes.tagline, 
        level_id=classes.level_id, 
        image_link=classes.image_link
    )
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

def get_class_by_level(db: Session, level_id: int):
    return db.query(Class).filter(Class.level_id == level_id, Class.is_deleted == False).all()
