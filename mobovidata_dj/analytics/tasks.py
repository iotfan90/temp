from celery import shared_task
from celery.utils.log import get_task_logger

from .models import CustomerDevice
from .views import LifecycleAnalytics, TrackingEmailSignUp
from mobovidata_dj.responsys.utils import ResponsysApi


logger = get_task_logger(__name__)


@shared_task(ignore_results=True)
def email_sign_up_track():
    """
    Celery task to update new email sign up and unsubscribe
    """
    TrackingEmailSignUp().download_files()


@shared_task(ignore_results=True)
def lifecycle_status():
    LifecycleAnalytics().get_lifecycle_status()


@shared_task(ignore_results=True)
def update_customer_devices():
    """
    Updates Responsys profile extension table (PET) from CustomerDevice table
    """
    customer_devices = CustomerDevice.objects.filter(uploaded=False)[:200]
    rg_devices = customer_devices.values_list('riid', 'device')
    fields = ['RIID_', 'DEVICE_']
    values = [v for v in map(list, rg_devices)]
    response = ResponsysApi().merge_update_pet_members('WELCOME_PET_INFO',
                                                       fields, values)
    if response.status_code == 200:
        for each in customer_devices:
            each.uploaded = True
            each.save()
