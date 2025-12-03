from app.sync_service import run_sync

if __name__ == "__main__":
    # Точка входа для cron-задачи или ручного запуска синка
    run_sync()
