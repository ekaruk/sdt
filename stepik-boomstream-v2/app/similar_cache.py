from threading import Lock, Thread
from typing import List, Optional
import time

from .db import SessionLocal
from .embeddings import upsert_question_embedding
from .models import Question, QuestionAnswer, QuestionEmbedding, QuestionStepikModule, StepikModule

_CACHE = {}
_LOCK = Lock()
_SESSION_START_KEY = "__session_start_ts__"


def get_session_start_ts() -> int:
    with _LOCK:
        ts = _CACHE.get(_SESSION_START_KEY)
        if not ts:
            ts = int(time.time())
            _CACHE[_SESSION_START_KEY] = ts
        return ts


def get_cached_similar_ids(question_id: int) -> Optional[List[int]]:
    with _LOCK:
        return _CACHE.get(question_id)


def set_cached_similar_ids(question_id: int, similar_ids: List[int]) -> None:
    with _LOCK:
        _CACHE[question_id] = list(similar_ids)


def _get_similar_questions_by_modules(db, question_id: int, module_ids: List[int], limit: int) -> List[int]:
    if not module_ids:
        return []
    rows = (
        db.query(QuestionStepikModule.question_id)
        .filter(
            QuestionStepikModule.module_id.in_(module_ids),
            QuestionStepikModule.question_id != question_id,
        )
        .distinct()
        .limit(limit)
        .all()
    )
    return [row[0] for row in rows]


def _get_similar_question_ids_by_embedding(db, question_id: int, embedding, limit: int) -> List[int]:
    try:
        rows = (
            db.query(QuestionEmbedding.question_id)
            .filter(QuestionEmbedding.question_id != question_id)
            .order_by(QuestionEmbedding.embedding.cosine_distance(embedding))
            .limit(limit)
            .all()
        )
        return [row[0] for row in rows]
    except Exception as e:
        print(f"[Embedding] Similar search failed: {e}")
        return []


def compute_similar_ids(db, question, modules, answer_summary, limit: int = 5) -> List[int]:
    embedding_row = (
        db.query(QuestionEmbedding)
        .filter(QuestionEmbedding.question_id == question.id)
        .first()
    )
    if not embedding_row:
        try:
            if upsert_question_embedding(db, question, modules, answer_summary):
                db.commit()
            embedding_row = (
                db.query(QuestionEmbedding)
                .filter(QuestionEmbedding.question_id == question.id)
                .first()
            )
        except Exception as e:
            print(f"[Embedding] Update failed: {e}")
            db.rollback()

    if embedding_row:
        similar_ids = _get_similar_question_ids_by_embedding(
            db, question.id, embedding_row.embedding, limit
        )
    else:
        similar_ids = []

    if not similar_ids:
        module_ids = [m.id for m in modules] if modules else []
        similar_ids = _get_similar_questions_by_modules(db, question.id, module_ids, limit)

    return similar_ids


def get_or_compute_similar_ids(db, question, modules, answer_summary, limit: int = 5) -> List[int]:
    cached = get_cached_similar_ids(question.id)
    if cached is not None:
        return cached

    similar_ids = compute_similar_ids(db, question, modules, answer_summary, limit)
    set_cached_similar_ids(question.id, similar_ids)
    return similar_ids


def refresh_similar_cache(question_id: int) -> None:
    db = SessionLocal()
    try:
        question = db.query(Question).filter_by(id=question_id).first()
        if not question:
            return
        modules = (
            db.query(StepikModule)
            .join(QuestionStepikModule)
            .filter(QuestionStepikModule.question_id == question_id)
            .order_by(StepikModule.position)
            .all()
        )
        answer = db.query(QuestionAnswer).filter_by(question_id=question_id).first()
        answer_summary = answer.summary if answer and getattr(answer, "summary", None) else None
        similar_ids = compute_similar_ids(db, question, modules, answer_summary, limit=5)
        set_cached_similar_ids(question_id, similar_ids)
    finally:
        db.close()


def refresh_similar_cache_async(question_id: int) -> None:
    Thread(target=refresh_similar_cache, args=(question_id,), daemon=True).start()


def warmup_similar_cache() -> None:
    db = SessionLocal()
    try:
        print("[Cache] Similar questions warmup started.")
        question_ids = [row[0] for row in db.query(Question.id).all()]
        for question_id in question_ids:
            if get_cached_similar_ids(question_id) is not None:
                continue
            question = db.query(Question).filter_by(id=question_id).first()
            if not question:
                continue
            modules = (
                db.query(StepikModule)
                .join(QuestionStepikModule)
                .filter(QuestionStepikModule.question_id == question_id)
                .order_by(StepikModule.position)
                .all()
            )
            answer = db.query(QuestionAnswer).filter_by(question_id=question_id).first()
            answer_summary = answer.summary if answer and getattr(answer, "summary", None) else None
            similar_ids = compute_similar_ids(db, question, modules, answer_summary, limit=5)
            set_cached_similar_ids(question_id, similar_ids)
        print(f"[Cache] Similar questions warmup finished. Cached: {len(question_ids)}.")
    except Exception as e:
        print(f"[Cache] Warmup failed: {e}")
    finally:
        db.close()


def warmup_similar_cache_async() -> None:
    Thread(target=warmup_similar_cache, daemon=True).start()
