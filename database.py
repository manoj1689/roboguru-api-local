from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Replace with your database URL


<<<<<<< HEAD
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:password@localhost:5432/robo_guru"
=======
SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:password@localhost:5432/roboguru"
>>>>>>> 69e201c15e1ea3e67d506f65ebbcef1ffa53f361
# SQLALCHEMY_DATABASE_URL= "postgresql://postgres:password@localhost:5432/roboguru"
engine = create_engine(SQLALCHEMY_DATABASE_URL)


# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
