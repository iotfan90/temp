# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from .views import (AftershipWebhookView, DojomojoWebhookView,
                    ShopifyWebhookView, UnbounceWebhookView)

urlpatterns = [
    url(r'^aftership/$', AftershipWebhookView.as_view(),
        name='aftership-webhook'),
    url(r'^dojomojo/$', DojomojoWebhookView.as_view(), name='dojomojo-webhook'),
    url(r'^shopify/$', ShopifyWebhookView.as_view(), name='shopify-webhook'),
    url(r'^unbounce/$', UnbounceWebhookView.as_view(), name='unbounce-webhook'),
]
