# Procfile for deployment platforms (Railway, Heroku, etc.)

web: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --log-level info
worker: celery -A app.core.celery worker --loglevel=info
beat: celery -A app.core.celery beat --loglevel=info
