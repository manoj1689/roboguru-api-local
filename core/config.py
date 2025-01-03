from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SECRET_KEY: str = "d4e3f87cfd9b57e1bc8e8459af1792842b7eec776b67654b5973b12ad7688e84"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./test.db"
    
    OPENAI_API_KEY: str = "your-openai-api-key"

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URL

