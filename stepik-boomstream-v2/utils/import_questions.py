

from app.db import engine, Base
from app.models import Question, StepikModule
from sqlalchemy.orm import sessionmaker

import csv
from datetime import datetime

# Список модулей по номеру раздела
module_map = {
    '1': 561993,
    '2': 579296,
    '3': 564649,
    '4': 579297,
    '5': 611382,
    '6': 611383,
}

csv_path = 'utils/upload_data/questions_structured.csv'

Session = sessionmaker(bind=engine)
session = Session()

with open(csv_path, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    count = 0
    for row in reader:
        section = row['section_number'].strip()
        module_id = module_map.get(section)
        module = session.query(StepikModule).filter_by(id=module_id).first() if module_id else None
        question = Question(
            body=row['question_text'].strip(),
            title=row['short_title'].strip(),
            status='VOTING',
            created_at=datetime.utcnow()
        )
        if module:
            question.modules.append(module)
        session.add(question)
        count += 1

session.commit()
print(f"Вопросы и связи с модулями успешно добавлены! Всего: {count}")
