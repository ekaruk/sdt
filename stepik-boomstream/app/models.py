from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    stepik_user_id = Column(Integer, unique=True, nullable=True)

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
