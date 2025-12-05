from stepik import StepikTablesAPI  
from app.db import Base, engine

if __name__ == "__main__":
    # на всякий случай убедиться, что таблицы созданы
    Base.metadata.create_all(bind=engine)

    api = StepikTablesAPI()
    api.sync_course_structure_to_db(clear_before=True)
