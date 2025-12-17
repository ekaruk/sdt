import sys
from pathlib import Path

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from stepik.stepik_tables_api import StepikTablesAPI  
from app.db import Base, engine

if __name__ == "__main__":
    # на всякий случай убедиться, что таблицы созданы
    Base.metadata.create_all(bind=engine)

    api = StepikTablesAPI()
    api.sync_course_structure_to_db(clear_before=True)
