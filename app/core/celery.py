"""Celery configuration for background tasks"""

from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "dreamduel",
    broker=settings.CELERY_BROKER_URL or f"{settings.REDIS_URL}/1",
    backend=settings.CELERY_RESULT_BACKEND or f"{settings.REDIS_URL}/2",
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks from all registered apps
celery_app.autodiscover_tasks(['app.core.tasks'])


# Example background tasks
@celery_app.task(name="send_email_async")
def send_email_async(recipient: str, subject: str, html_content: str):
    """Send email asynchronously"""
    from app.infrastructure.external_services.email_service import email_service
    
    try:
        email_service.send_email(
            recipient=recipient,
            subject=subject,
            html_content=html_content
        )
        return {"status": "success", "recipient": recipient}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@celery_app.task(name="process_analytics_batch")
def process_analytics_batch(events: list):
    """Process analytics events in batches"""
    from app.infrastructure.database.session import SessionLocal
    from app.infrastructure.database.models import AnalyticsEvent
    
    db = SessionLocal()
    try:
        # Batch insert analytics events
        db_events = [AnalyticsEvent(**event) for event in events]
        db.bulk_save_objects(db_events)
        db.commit()
        return {"status": "success", "events_processed": len(events)}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="cleanup_expired_tokens")
def cleanup_expired_tokens():
    """Clean up expired refresh tokens from Redis"""
    from app.infrastructure.cache.redis_client import redis_client
    
    # TODO: Implement token cleanup logic
    # This would scan Redis for expired tokens and remove them
    return {"status": "success", "note": "TODO: Implement cleanup logic"}


@celery_app.task(name="send_subscription_reminder")
def send_subscription_reminder(user_id: int):
    """Send subscription expiration reminder"""
    from app.infrastructure.database.session import SessionLocal
    from app.infrastructure.database.models import User
    from app.infrastructure.external_services.email_service import email_service
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "error", "message": "User not found"}
        
        html_content = f"""
        <h2>Subscription Reminder</h2>
        <p>Hi {user.username},</p>
        <p>Your DreamDuel subscription is about to expire.</p>
        <p>Renew now to continue creating amazing AI-generated stories!</p>
        """
        
        email_service.send_email(
            recipient=user.email,
            subject="Your DreamDuel Subscription",
            html_content=html_content
        )
        
        return {"status": "success", "user_id": user_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


# Periodic tasks (requires celery beat)
celery_app.conf.beat_schedule = {
    'cleanup-tokens-every-hour': {
        'task': 'cleanup_expired_tokens',
        'schedule': 3600.0,  # Every hour
    },
}
