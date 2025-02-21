from sqlalchemy import Column, Boolean, DateTime
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from database import Base


class BaseMixin:
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower() 