import copy
import json
import logging

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .models import WebhookTransaction

logger = logging.getLogger(__name__)


class WebhookBase(View):
    """
    Abstract Class
    Base webhook implementation
    Must implement process_webhook method
    """
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(WebhookBase, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        meta = copy.copy(request.META)

        for k, v in list(meta.items()):
            if not isinstance(v, str):
                del meta[k]

        obj = WebhookTransaction(request_meta=meta)
        self.process_webhook(request, obj)

        try:
            obj.full_clean()
        except ValidationError as ex:
            logger.exception('Webhook ValidationError', extra=locals())
            return HttpResponse(status=404)
        else:
            obj.save()
        return HttpResponse(status=200)

    def process_webhook(self, request, webhook_transaction):
        raise NotImplementedError

    class Meta:
        abstract = True


class AftershipWebhookView(WebhookBase):
    """
    Aftership webhook
    """
    def process_webhook(self, request, webhook_transaction):
        data = json.loads(request.body.decode('utf-8'))
        webhook_transaction.body = data
        webhook_transaction.webhook_type = WebhookTransaction.AFTERSHIP
        webhook_transaction.save()


class DojomojoWebhookView(WebhookBase):
    """
    DojoMojo webhook
    """
    def process_webhook(self, request, webhook_transaction):
        data = json.loads(request.body.decode('utf-8'))
        webhook_transaction.body = data
        webhook_transaction.webhook_type = WebhookTransaction.DOJOMOJO


class ShopifyWebhookView(WebhookBase):
    """
    Shopify webhook
    """
    def process_webhook(self, request, webhook_transaction):
        data = json.loads(request.body.decode('utf-8'))
        webhook_transaction.body = data
        webhook_transaction.webhook_type = WebhookTransaction.SHOPIFY
        webhook_transaction.save()


class UnbounceWebhookView(WebhookBase):
    """
    Unbounce webhook
    """
    def process_webhook(self, request, webhook_transaction):
        data = json.loads(request.POST['data.json'].decode('utf-8'))
        webhook_transaction.body = data
        webhook_transaction.webhook_type = WebhookTransaction.UNBOUNCE
        webhook_transaction.save()
