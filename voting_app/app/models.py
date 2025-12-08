from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from sqlalchemy.types import JSON

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Telegram ID пользователя (главный идентификатор)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)

    email = Column(String, unique=True, nullable=True)

    # смещение от UTC в часах (например, +3 для Москвы)
    timezone_offset_hours = Column(Integer, nullable=False, default=0)

    # расписание в формате {"mon":[0,1,2], "tue":[...]} — ВСЕ ЧАСЫ В UTC
    schedule_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
