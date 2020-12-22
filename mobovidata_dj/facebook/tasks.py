from datetime import datetime, timedelta
from celery import shared_task
from celery.utils.log import get_task_logger

from .connect import FacebookConnect

logger = get_task_logger(__name__)


@shared_task(ignore_results=True)
def update_facebook_ads_status():
    """
    Celery task to update facebook ads status
    :return:
    """
    FacebookConnect().read_update_ads()


@shared_task(ignore_results=True)
def update_todays_stats():
    """
    Celery task to update today's facebook ads stats
    :return:
    """
    from .models import AdStatWindow
    AdStatWindow.build_stats()


@shared_task(ignore_results=True)
def update_last_thirty_days_stats():
    """
    Updates facebook insights for the last 30 days. Run nightly.
    :return:
    """
    # Loop over today-> 30 days before today and generate ad insights.
    from .models import AdStatWindow
    for i in range(1, 30):
        dt = datetime.now() - timedelta(days=i)
        AdStatWindow.build_stats('%s' % dt.date())
