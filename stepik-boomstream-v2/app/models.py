from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint, BigInteger, Text, Boolean, Index, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base
from pgvector.sqlalchemy import Vector


# Константы ролей
ROLE_USER = 0      # Пользователь - базовые права
ROLE_CURATOR = 1   # Куратор - расширенные права
ROLE_ADMIN = 2     # Админ - полные права

ROLE_NAMES = {
    ROLE_USER: 'Пользователь',
    ROLE_CURATOR: 'Куратор',
    ROLE_ADMIN: 'Админ'
}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    boom_password = Column(String(32), nullable=True)
    stepik_user_id = Column(BigInteger, unique=True, nullable=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True)
    google_sub = Column(String, nullable=True)
    video_access = Column(Integer, nullable=False, default=0, server_default="0")
    stepik_lesson_id = Column(Integer, nullable=True)
    stepik_step_id = Column(Integer, nullable=True)
    role = Column(Integer, nullable=False, default=0, server_default="0")  # 0=user, 1=curator, 2=admin
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_users_role', 'role'),
    )
    
    def is_curator(self):
        """Проверка прав куратора (куратор или админ)."""
        return self.role >= ROLE_CURATOR
    
    def is_admin(self):
        """Проверка прав администратора."""
        return self.role >= ROLE_ADMIN
    
    def get_role_name(self):
        """Получить текстовое название роли."""
        return ROLE_NAMES.get(self.role, 'Неизвестно')




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
    short_title = Column(String, nullable=True)  # Короткое название для компактного отображения
    position = Column(Integer, nullable=False)
    forum_topic_icon = Column(String, nullable=True)  # Custom emoji ID для иконки форум-топика

    def __repr__(self):
        return f"<StepikModule id={self.id} title={self.title}>"


class StepikLesson(Base):
    __tablename__ = "stepik_lessons"

    id = Column(Integer, primary_key=True, index=True)

    module_id = Column(Integer, ForeignKey("stepik_modules.id"), nullable=False)

    title = Column(String, nullable=False)
    position = Column(Integer, nullable=False)
    boom_media = Column(String, nullable=True)
    steps_amount = Column(Integer, nullable=True)

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


class TelegramMessage(Base):
    __tablename__ = "telegram_messages"

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_thread_id = Column(Integer, nullable=True)
    message_id = Column(Integer, nullable=False)
    ref_type = Column(String, nullable=True)
    ref_id = Column(Integer, nullable=True)
    text = Column(Text, nullable=True)
    reply_markup = Column(Text, nullable=True)
    parse_mode = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_telegram_messages_chat_message', 'chat_id', 'message_id'),
    )

# ============================================================================
# QUESTIONS SYSTEM MODELS
# ============================================================================

class Question(Base):
    """Основная таблица вопросов со статусами жизненного цикла."""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=True)  # опциональный заголовок
    body = Column(Text, nullable=False)  # текст вопроса
    
    # Жизненный цикл: VOTING → SCHEDULED → POSTED → CLOSED → ARCHIVED
    status = Column(String(20), nullable=False, default='VOTING')
    
    # Автор вопроса
    author_telegram_id = Column(BigInteger, ForeignKey('telegram_users.id'), nullable=True)
    
    # Временные метки жизненного цикла
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    posted_at = Column(DateTime, nullable=True)  # когда опубликован в Telegram
    closed_at = Column(DateTime, nullable=True)  # когда закрыто обсуждение
    archived_at = Column(DateTime, nullable=True)  # когда добавлен итоговый ответ
    
    # Индексы для оптимизации запросов
    __table_args__ = (
        Index('idx_questions_status_created', 'status', 'created_at'),
    )


    # Many-to-many: Question <-> StepikModule
    modules = relationship(
        "StepikModule",
        secondary="question_stepik_modules",
        backref="questions",
        lazy="joined"
    )


    votes_count = Column(Integer, default=0, nullable=False)
    embedding = relationship("QuestionEmbedding", uselist=False, back_populates="question")

    def __repr__(self):
        return f"<Question id={self.id} status={self.status} title={self.title[:30] if self.title else 'Untitled'}>"


class QuestionEmbedding(Base):
    __tablename__ = "question_embeddings"

    question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), primary_key=True)
    embedding = Column(Vector(3072), nullable=False)
    source_text = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    question = relationship("Question", back_populates="embedding")

    def __repr__(self):
        return f"<QuestionEmbedding question_id={self.question_id} updated_at={self.updated_at}>"


class QuestionStepikModule(Base):
    """Many-to-Many связь между вопросами и модулями Stepik (темами курса)."""
    __tablename__ = "question_stepik_modules"

    question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), primary_key=True)
    module_id = Column(Integer, ForeignKey('stepik_modules.id', ondelete='CASCADE'), primary_key=True)
    
    # Опционально: пометка основной темы для вопроса
    is_primary = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Индекс для быстрой фильтрации по модулю
    __table_args__ = (
        Index('idx_question_modules_module', 'module_id'),
    )

    def __repr__(self):
        return f"<QuestionStepikModule question_id={self.question_id} module_id={self.module_id}>"


class QuestionVote(Base):
    """Голоса (лайки) пользователей за вопросы. Один пользователь = один голос."""
    __tablename__ = "question_votes"

    question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), primary_key=True)
    telegram_user_id = Column(BigInteger, ForeignKey('telegram_users.id', ondelete='CASCADE'), primary_key=True)
    
    voted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Индексы для оптимизации
    __table_args__ = (
        Index('idx_question_votes_count', 'question_id'),
        Index('idx_question_votes_user', 'telegram_user_id', 'question_id'),
    )

    def __repr__(self):
        return f"<QuestionVote question_id={self.question_id} user_id={self.telegram_user_id}>"


class TelegramTopic(Base):
    """Техническая привязка вопроса к теме (Forum Topic) в Telegram."""
    __tablename__ = "telegram_topics"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # Telegram данные
    chat_id = Column(BigInteger, nullable=False)  # ID форум-группы
    message_thread_id = Column(Integer, nullable=False)  # ID темы в форуме
    
    # Временные метки жизненного цикла темы
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    close_at = Column(DateTime, nullable=False)  # когда нужно закрыть (opened_at + 7 days)
    closed_at = Column(DateTime, nullable=True)  # фактическое время закрытия
    
    # Message IDs для возможности редактирования/удаления
    open_message_id = Column(Integer, nullable=True)  # ID стартового поста
    close_message_id = Column(Integer, nullable=True)  # ID финального поста
    notice_message_id = Column(Integer, nullable=True)  # ID уведомления
    notice_is_pinned = Column(Boolean, nullable=False, default=False, server_default="false")
    
    # Статистика
    messages_count = Column(Integer, default=1, nullable=False)  # Количество сообщений в теме
    
    # Индекс для cron job'а закрытия тем
    __table_args__ = (
        Index('idx_telegram_topics_close', 'close_at', 'closed_at'),
    )

    def __repr__(self):
        return f"<TelegramTopic question_id={self.question_id} thread_id={self.message_thread_id} closed={self.closed_at is not None}>"


class QuestionAnswer(Base):
    """Итоговые ответы после обсуждения (база знаний)."""
    __tablename__ = "question_answers"

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    # Контент ответа
    summary = Column(String(500), nullable=False)  # краткий итог для карточки (1-3 предложения)
    answer = Column(Text, nullable=False)  # полный структурированный ответ
    
    # Источники (JSON: ссылки на уроки, сообщения в Telegram, внешние ссылки)
    sources = Column(JSON, nullable=True)
    # Пример: {"lessons": [123, 456], "telegram_messages": [789], "external_links": ["https://..."]}
    
    # Метаданные
    author_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # кто написал итог (модератор)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Опционально: была ли опубликована в Telegram
    published_to_telegram = Column(Boolean, default=False)
    telegram_message_id = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<QuestionAnswer question_id={self.question_id} summary={self.summary[:50]}...>"
