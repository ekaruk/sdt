from datetime import datetime
from typing import Iterable, Optional, Tuple

from openai import OpenAI
from sqlalchemy.orm import Session

from .config import Config
from .models import Question, QuestionEmbedding, StepikModule


def get_embedding_model_and_dims() -> Tuple[str, int]:
    model = getattr(Config, "OPENAI_EMBEDDING_MODEL", None) or "text-embedding-3-large"
    dims_value = getattr(Config, "OPENAI_EMBEDDING_DIM", None)
    if dims_value:
        return model, int(dims_value)
    if model.endswith("small"):
        return model, 1536
    if model.endswith("large"):
        return model, 3072
    return model, 3072


def build_question_source_text(
    question: Question, modules: Iterable[StepikModule], answer_summary: Optional[str] = None
) -> str:
    module_titles = [m.short_title or m.title for m in modules if m]
    parts = []
    if module_titles:
        parts.append("Разделы: " + "; ".join(module_titles))
    if question.title:
        # Boost title signal by repeating it.
        parts.append("Заголовок: " + question.title)
        parts.append("Заголовок: " + question.title)
    parts.append("Текст: " + question.body)
    if answer_summary:
        parts.append("Ответ: " + answer_summary)
    return "\n".join(parts).strip()


def generate_embedding(text: str) -> Optional[list]:
    if not Config.OPENAI_API_KEY:
        return None
    model, _ = get_embedding_model_and_dims()
    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    response = client.embeddings.create(model=model, input=text)
    return response.data[0].embedding


def upsert_question_embedding(
    db: Session,
    question: Question,
    modules: Iterable[StepikModule],
    answer_summary: Optional[str] = None,
) -> bool:
    source_text = build_question_source_text(question, modules, answer_summary)
    existing = (
        db.query(QuestionEmbedding)
        .filter(QuestionEmbedding.question_id == question.id)
        .first()
    )
    if existing and existing.source_text == source_text:
        return False

    embedding = generate_embedding(source_text)
    if embedding is None:
        return False

    if existing:
        existing.embedding = embedding
        existing.source_text = source_text
        existing.updated_at = datetime.utcnow()
    else:
        db.add(
            QuestionEmbedding(
                question_id=question.id,
                embedding=embedding,
                source_text=source_text,
                updated_at=datetime.utcnow(),
            )
        )
    return True
