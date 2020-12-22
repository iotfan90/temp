# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views
import mobovidata_dj.analytics.views


urlpatterns = [
    url(regex=r'^tracking\.gif$', view=views.tracking, name='tracking'),
    url(regex=r'^register_user$', view=views.register_user,
        name='register_user'),
    url(regex=r'^eval_user$', view=views.eval_user, name='eval_user'),
    url(regex=r'^check_uuid$', view=views.check_uuid, name='check_uuid'),
    url(r'^recent-pageviews/$', mobovidata_dj.analytics.views.recent_pageviews,
        name='recent-pageviews'),
    url(r'^gmail-ads$', views.GmailAds.as_view(), name='gmail_ads'),
    url(r'^lead-gens/$', mobovidata_dj.analytics.views.LeadGenEmails.as_view(),
        name='lead-gens'),
    url(r'^mobovida-email$', views.mobovida_email_signup,
        name='mobovida-email'),
    url(r'^track-signup$', views.mobovida_email_signup, name='track-signup'),
    url(r'^md5-optout/$', views.check_md5_emails, name='check-md5-emails'),
    url(r'^email-signup-track/$',
        mobovidata_dj.analytics.views.TrackingEmailSignUp.as_view(),
        name='sign-up-track'),
    url(r'^sms/$', mobovidata_dj.analytics.views.TextSignUp.as_view(),
        name='sms'),
    url(r'^customer-dashboard/$',
        mobovidata_dj.analytics.views.CustomerDashboard.as_view(),
        name='customer-dashboard'),
    url(r'^customer-dashboard/(?P<email>[\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4})/$', mobovidata_dj.analytics.views.CustomerDashboard.as_view(), name='customer-dashboard'),
    url(r'^customer-email/$',
        mobovidata_dj.analytics.views.CustomerEmail.as_view(),
        name='customer-email'),
    url(r'^open-purchase-orders/$',
        mobovidata_dj.analytics.views.open_purchase_orders,
        name='open-purchase-orders'),
    url(r'^lifecycle-analytics/$',
        mobovidata_dj.analytics.views.LifecycleAnalytics.as_view(),
        name='lifecycle-analytics'),
    url(r'^order_lookup/$', mobovidata_dj.analytics.views.OrderLookup.as_view(),
        name='order-lookup'),
    url(r'^order_details/$',
        mobovidata_dj.analytics.views.OrderDetails.as_view(),
        name='order-details'),
    url(r'^send-order-cancel/$',
        mobovidata_dj.analytics.views.send_order_cancellation_email,
        name='send-order-cancel'),
    url(r'^get-riid$', mobovidata_dj.analytics.views.get_riid, name='get-riid'),
    url(r'^get-customer-orders/$',
        mobovidata_dj.analytics.views.get_customer_info,
        name='get-customer-orders'),
    url(r'^dynamic-yield-email/$',
        mobovidata_dj.analytics.views.email_optin, name='email-optin'),

]
