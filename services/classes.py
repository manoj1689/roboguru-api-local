from sqlalchemy.orm import Session
from models import EducationLevel, Class
from schemas import ClassCreate
from fastapi import HTTPException
from typing import List, Optional
from fastapi.responses import JSONResponse

def get_class(db: Session, class_id: int):
    return db.query(Class).filter(Class.id == class_id).first()


def get_all_classes(db: Session, limit: int = 10, name: Optional[str] = None):
    query = db.query(Class).filter(
        Class.is_deleted == False
        )
    if name:
        query = query.filter(Class.name.ilike(f"%{name}%"))
    
    return query.limit(limit).all()


def create_class_in_db(db: Session, classes: ClassCreate):
    existing_class = db.query(EducationLevel).filter(EducationLevel.id == classes.level_id).first()
    if not existing_class:
        raise HTTPException(status_code=400, detail="Class already exists")

    db_class = Class(name=classes.name, tagline=classes.tagline, level_id=classes.level_id, image_link=classes.image_link)
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

def create_response(success: bool, message: str, data: dict = None):
    return JSONResponse(
        status_code=200 if success else 400,
        content={
            "success": success,
            "message": message,
            "data": data if data is not None else {}
        }
    )

# Get classes by education level ID
def get_class_by_level(db: Session, level_id: int):
    return db.query(Class).filter(Class.level_id == level_id, Class.is_deleted == False).all()


