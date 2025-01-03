from sqlalchemy.orm import Session
from models import EducationLevel
from schemas import EducationLevelCreate
from fastapi import HTTPException
from typing import List, Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import joinedload


def create_education_level(db: Session, level: EducationLevelCreate):
    existing_level = db.query(EducationLevel).filter(EducationLevel.name == level.name).first()
    if existing_level:
        raise HTTPException(status_code=400, detail="Education level already exists")

    db_level = EducationLevel(name=level.name, description=level.description)
    db.add(db_level)
    db.commit()
    db.refresh(db_level)
    return db_level


def get_education_level(db: Session, level_id: int):
    return db.query(EducationLevel).filter(
        EducationLevel.id == level_id, 
        EducationLevel.is_deleted == False
        ).first()

def get_all_education_levels(db: Session, limit: int = 10, name: Optional[str] = None):
    query = db.query(EducationLevel).filter(
        EducationLevel.is_deleted == False
        )
    if name:
        query = query.filter(EducationLevel.name.ilike(f"%{name}%"))
    
    return query.limit(limit).all()

