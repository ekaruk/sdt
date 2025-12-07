from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    boom_password = Column(String(32), nullable=True)
    stepik_user_id = Column(BigInteger, unique=True, nullable=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True)
    google_sub = Column(String, unique=True, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)




class VideoGrant(Base):
    __tablename__ = "video_grants"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stepik_lesson_id = Column(Integer, nullable=False)
    boomstream_resource_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    
class StepikModule(Base):
    __tablename__ = "stepik_modules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    position = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<StepikModule id={self.id} title={self.title}>"


class StepikLesson(Base):
    __tablename__ = "stepik_lessons"

    id = Column(Integer, primary_key=True, index=True)

    module_id = Column(Integer, ForeignKey("stepik_modules.id"), nullable=False)

    title = Column(String, nullable=False)
    position = Column(Integer, nullable=False)
    boom_media = Column(String, nullable=True)

    # связь: урок принадлежит модулю
    #module = relationship("StepikModule", back_populates="lessons")

    def __repr__(self):
        return f"<StepikLesson id={self.id} module={self.module_id} title={self.title}>"    

class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id = Column(BigInteger, primary_key=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    def __repr__(self):
        return (
            f"<TelegramUser id={self.id} username={self.username} "
            f"name={self.first_name} {self.last_name}>"
        )