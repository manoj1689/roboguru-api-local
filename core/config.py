from pydantic_settings import BaseSettings
from typing import ClassVar

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    SQLALCHEMY_DATABASE_URL: str
    TRENDING_TOPICS_LIMIT: ClassVar[int] = 3
    OPENAI_API_KEY: str
    SUPERADMIN_UID: str

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
