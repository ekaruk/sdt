from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    # boom_password (9 цифр) можно хранить как строку, если нужно:
    boom_password = Column(String(32), nullable=True)
    stepik_user_id = Column(BigInteger, unique=True, nullable=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True)
    google_sub = Column(String, unique=True, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    grants = relationship("VideoGrant", back_populates="user")


class VideoGrant(Base):
    __tablename__ = "video_grants"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stepik_lesson_id = Column(Integer, nullable=False)
    boomstream_resource_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="grants")

    __table_args__ = (
        UniqueConstraint("user_id", "stepik_lesson_id", "boomstream_resource_id"),
    )
    
class StepikModule(Base):
    __tablename__ = "stepik_modules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    position = Column(Integer, nullable=False)

    # связь: один модуль → много уроков
    lessons = relationship(
        "StepikLesson",
        back_populates="module",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<StepikModule id={self.id} title={self.title}>"


class StepikLesson(Base):
    __tablename__ = "stepik_lessons"

    id = Column(Integer, primary_key=True, index=True)

    module_id = Column(Integer, ForeignKey("stepik_modules.id"), nullable=False)

    title = Column(String, nullable=False)
    position = Column(Integer, nullable=False)

    # связь: урок принадлежит модулю
    module = relationship("StepikModule", back_populates="lessons")

    def __repr__(self):
        return f"<StepikLesson id={self.id} module={self.module_id} title={self.title}>"    
