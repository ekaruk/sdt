import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# По умолчанию SQLite-файл, можно переопределить через переменную окружения DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./voting.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    future=True,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()
