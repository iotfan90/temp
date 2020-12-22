# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from .views import (campaign_preview, CustomersCanceledOrder, ProductReview,
                    ProductReviewsReport)


urlpatterns = [
    # Lifecycle
    url(r'^campaign-preview/$', campaign_preview, name='campaign-preview'),
    url(r'^exclude-canceled-order', CustomersCanceledOrder.as_view(),
        name='exclude-canceled-order'),
    # url(r'^product-review/(?P<order_id>[\w\-]+)/(?P<product_id>[\w\-]+)/$', ProductReview.as_view(), name='product-review'),
    url(r'^product-review/(?P<product_id>[^/]+)/(?P<order_id>[^/]+)/(?P<riid>[^/]+)/$',
        ProductReview.as_view(), name='product-review'),
    url(r'^product-review/$', ProductReview.as_view(), name='product-review'),
    url(r'^product-review-api/REVIEW-DATE/(?P<year>[^/]+)/(?P<month>[^/]+)/(?P<day>[^/.]+)(.json)?/$',
        ProductReviewsReport.as_view(), name='product-reviews-report'),
]
