from celery import shared_task
from celery.utils.log import get_task_logger

from .views import HelpScoutEmails

logger = get_task_logger(__name__)


@shared_task(ignore_results=True)
def update_helpscout():
    """
    Celery task to get helpscout email list for past 24 hours
    """
    HelpScoutEmails().update_helpscout()
