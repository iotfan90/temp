import traceback

from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.forms import modelformset_factory
from datetime import datetime

from .forms import DojomojoModelForm, UnbounceModelForm
from .models import Dojomojo, WebhookTransaction
from .utils import get_data_as_formset

from mobovidata_dj.lifecycle.models import ShippingStatusTracking
from mobovidata_dj.shopify.webhook import process_webhook

logger = get_task_logger(__name__)


@shared_task(ignore_results=True)
def aftership_process():
    """
    Process aftership webhooks
    @return void
    """
    webhooks = (WebhookTransaction.objects
                .filter(webhook_type=WebhookTransaction.AFTERSHIP,
                        status=WebhookTransaction.UNPROCESSED)
                .order_by('date_received'))

    for webhook in webhooks:

        try:
            content = webhook.body['msg']
            ShippingStatusTracking.objects.update_or_create(
                order_id=content['order_id'],
                defaults={'event': content['tag'],
                          'courier': content['slug'],
                          'tracking_number': content['tracking_number']}
            )
            webhook.status = WebhookTransaction.PROCESSED
        except Exception as e:
            webhook.status = WebhookTransaction.ERROR
            tb = traceback.format_exc()
            error_msg = 'Aftership processing task error | %s | %s' % (e, tb)
            webhook.error_msg = error_msg
            logger.exception('Aftership processing task error', extra=locals())
        finally:
            webhook.date_processed = timezone.now()
            webhook.save()


@shared_task(ignore_results=True)
def dojomojo_process():
    """
    Process dojomojo webhooks
    @return void
    """
    webhooks = (WebhookTransaction.objects
                .filter(webhook_type=WebhookTransaction.DOJOMOJO,
                        status=WebhookTransaction.UNPROCESSED)
                .order_by('date_received'))

    for webhook in webhooks:

        try:
            dojomojoFormSet = modelformset_factory(Dojomojo,
                                                   form=DojomojoModelForm)
            dojomojo_len = str(len(webhook.body))
            data = get_data_as_formset(webhook.body, total_forms=dojomojo_len)
            formset = dojomojoFormSet(data)
            if formset.is_valid():
                webhook.status = WebhookTransaction.PROCESSED
                instances = formset.save()
            else:
                webhook.status = WebhookTransaction.ERROR
                webhook.error_msg = formset.errors
        except Exception as e:
            webhook.status = WebhookTransaction.ERROR
            tb = traceback.format_exc()
            error_msg = 'Dojomojo processing task error | %s | %s' % (e, tb)
            webhook.error_msg = error_msg
            logger.exception('Dojomojo processing task error', extra=locals())
        finally:
            webhook.date_processed = timezone.now()
            webhook.save()


@shared_task(ignore_results=True)
def shopify_process():
    """
    Process shopify webhooks
    @return void
    """
    webhooks = (WebhookTransaction.objects
                .filter(webhook_type=WebhookTransaction.SHOPIFY,
                        status=WebhookTransaction.UNPROCESSED)
                .order_by('date_received'))

    for webhook in webhooks:
        try:
            shopify_domain = webhook.request_meta['HTTP_X_SHOPIFY_SHOP_DOMAIN']
            topic = webhook.request_meta['HTTP_X_SHOPIFY_TOPIC']
            content = webhook.body
            process_webhook(shopify_domain, topic, content)
            webhook.status = WebhookTransaction.PROCESSED
        except Exception as e:
            webhook.status = WebhookTransaction.ERROR
            tb = traceback.format_exc()
            error_msg = 'Shopify webhook processing error | {} | {}'.format(e,
                                                                            tb)
            webhook.error_msg = error_msg
            logger.exception('Shopify webhook processing error', extra=locals())
        finally:
            webhook.date_processed = timezone.now()
            webhook.save()


@shared_task(ignore_results=True)
def unbounce_process():
    """
    Process unbounce webhooks
    @return void
    """
    webhooks = (WebhookTransaction.objects
                .filter(webhook_type=WebhookTransaction.UNBOUNCE,
                        status=WebhookTransaction.UNPROCESSED)
                .order_by('date_received'))

    for webhook in webhooks:

        try:
            data = {key: value[0] for (key, value) in webhook.body.iteritems()}
            data['time_submitted'] = datetime.strptime(data['time_submitted'],
                                                       '%I:%M %p UTC').time()
            form = UnbounceModelForm(data)

            if form.is_valid():
                webhook.status = WebhookTransaction.PROCESSED
                form.save()
            else:
                webhook.status = WebhookTransaction.ERROR
                webhook.error_msg = form.errors
        except Exception as e:
            webhook.status = WebhookTransaction.ERROR
            tb = traceback.format_exc()
            error_msg = 'Unbounce processing task error | %s | %s' % (e, tb)
            webhook.error_msg = error_msg
            logger.exception('Unbounce processing task error', extra=locals())
        finally:
            webhook.date_processed = timezone.now()
            webhook.save()
