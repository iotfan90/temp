# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views import defaults as default_views
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from mobovidata_dj.lifecycle.views import SendOrderConfirmationEmail


urlpatterns = [
    url(r'^$',
        login_required(TemplateView.as_view(template_name='pages/home.html')),
        name="home"),
    url(r'^about/$',
        TemplateView.as_view(template_name='pages/about.html'), name="about"),
    # url(r'^', include('mobovidata_dj.users.urls', namespace="users")),
    # Django Admin, use {% url 'admin:index' %}
    url(settings.ADMIN_URL, include(admin.site.urls)),
    url(
        r'^favicon-',
        RedirectView.as_view(
            url=staticfiles_storage.url('/images/favicon.ico'),
            permanent=False),
        name="favicon"
    ),
    # User management
    url(r'^users/', include("mobovidata_dj.users.urls", namespace="users")),
    url(r'^accounts/', include('allauth.urls')),
    # url('^registration/', include('registration.urls')),

    # Your stuff: custom urls includes go here
    url(r'^api/', include('mobovidata_dj.analytics.urls',
                          namespace="analytics")),
    url(r'^responsys/', include('mobovidata_dj.responsys.urls',
                                namespace="responsys")),

    # Lifecycle views
    url(r'lifecycle/', include('mobovidata_dj.lifecycle.urls',
                               namespace='lifecycle')),
    url(r'facebook/', include('mobovidata_dj.facebook.urls',
                              namespace='facebook')),
    url(r'shopify/', include('mobovidata_dj.shopify.urls',
                              namespace='shopify')),
    url(r'^webhooks/', include('mobovidata_dj.webhooks.urls',
                               namespace='wehbook')),
    url(r'export-report/', include('mobovidata_dj.reports.urls',
                                   namespace='reports')),
    url(r'^sendemailconfirm/',
        SendOrderConfirmationEmail.as_view(),
        name='sendemail'),

    # Image Retrieval
    url(r'image-retrieval/', include('mobovidata_dj.imageretrieval.urls',
                                     namespace='image-retrieval')),
    # include application views
    url(r'sales/', include('mobovidata_dj.salesreport.urls',
                           namespace='sales')),
    url(r'helpscout/', include('mobovidata_dj.helpscout.urls',
                               namespace='helpscout')),
    url(r'feeds/', include('mobovidata_dj.feeds.urls', namespace='feeds')),
    url(r'kpi/', include('kpi.urls', namespace='kpi')),
    url(r'ltv/', include('mobovidata_dj.ltv.urls', namespace='ltv')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        url(r'^400/$', default_views.bad_request,
            kwargs={'exception': Exception("Bad Request!")}),
        url(r'^403/$', default_views.permission_denied,
            kwargs={'exception': Exception("Permission Denied")}),
        url(r'^404/$', default_views.page_not_found,
            kwargs={'exception': Exception("Page not Found")}),
        url(r'^500/$', default_views.server_error),
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
