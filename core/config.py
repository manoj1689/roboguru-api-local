from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    SQLALCHEMY_DATABASE_URL: str = os.getenv("SQLALCHEMY_DATABASE_URL")
    TRENDING_TOPICS_LIMIT: int = 3
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    SUPERADMIN_UID: str = os.getenv("SUPERADMIN_UID")

settings = Settings()
