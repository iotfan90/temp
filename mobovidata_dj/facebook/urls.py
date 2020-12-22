from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from django.views.generic import TemplateView

from .views import (FacebookAdCreator, FacebookAdPreview, FacebookAdUpload,
                    FacebookImageUpload, FacebookLogin,
                    FacebookMultipleAdCreator, FacebookMultipleAdPreview,
                    FacebookShopifyAdCreator, FacebookShopifyAdPreview,
                    FacebookShopifyImageUpload, FacebookShopifyAdUpload,
                    FacebookAPICredentialsSelector,
                    FacebookShopifyAPICredentialsSelector)


urlpatterns = [
    # Facebook carousel ads views
    url(r'^ad-login/$', FacebookLogin.as_view(), name='ad-login'),

    url(r'^ad-api-selector/$', FacebookAPICredentialsSelector.as_view(),
        name='ad-api-selector'),
    url(r'^ad-creator/$', FacebookAdCreator.as_view(), name='ad-creator'),
    url(r'^multiple-ad-creator/$', FacebookMultipleAdCreator.as_view(),
        name='multiple-ad-creator'),
    url(r'^multiple-ad-preview/$', FacebookMultipleAdPreview.as_view(),
        name='multiple-ad-preview'),
    url(r'^ad-preview/$', FacebookAdPreview.as_view(), name='ad-preview'),
    url(r'^ad-upload/$', FacebookAdUpload.as_view(), name='ad-upload'),
    url(r'^image-upload/$', FacebookImageUpload.as_view(), name='image-upload'),
    url(r'^ad-preview/mobovidata/starrating/$',
        TemplateView.as_view(template_name='starrating.html'),
        name='starrating'),

    url(r'^shopify-ad-api-selector/$',
        FacebookShopifyAPICredentialsSelector.as_view(),
        name='shopify-ad-api-selector'),
    url(r'^shopify/ad-creator/$', FacebookShopifyAdCreator.as_view(),
        name='shopify-ad-creator'),
    url(r'^shopify-ad-preview/$', FacebookShopifyAdPreview.as_view(),
        name='shopify-ad-preview'),
    url(r'^shopify-image-upload/$', FacebookShopifyImageUpload.as_view(),
        name='shopify-image-upload'),
    url(r'^shopify-ad-upload/$', FacebookShopifyAdUpload.as_view(),
        name='shopify-ad-upload'),
]
