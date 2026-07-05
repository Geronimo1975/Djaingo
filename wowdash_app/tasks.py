from celery import shared_task


@shared_task
def ping():
    """Health task to verify Celery wiring."""
    return 'pong'
