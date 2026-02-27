# Procfile for deployment platforms (Railway, Heroku, etc.)

web: alembic upgrade head && gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --log-level info

# Background workers (opcional - descomentar cuando configures Celery)
# worker: celery -A app.core.celery worker --loglevel=info
# beat: celery -A app.core.celery beat --loglevel=info
