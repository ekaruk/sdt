import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db import SessionLocal
from app.models import Question, StepikModule, QuestionStepikModule
from app.embeddings import upsert_question_embedding


def main() -> None:
    db = SessionLocal()
    try:
        questions = db.query(Question).all()
        total = len(questions)
        updated = 0
        print(f"Found questions: {total}")
        for idx, question in enumerate(questions, start=1):
            modules = (
                db.query(StepikModule)
                .join(QuestionStepikModule)
                .filter(QuestionStepikModule.question_id == question.id)
                .order_by(StepikModule.position)
                .all()
            )
            if upsert_question_embedding(db, question, modules):
                updated += 1
                if updated % 20 == 0:
                    db.commit()
            if idx % 20 == 0 or idx == total:
                print(f"Processed {idx}/{total}, updated {updated}")
        db.commit()
        print(f"Updated embeddings: {updated}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
