# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

import mobovidata_dj.ltv.views

urlpatterns = [
    url(r'^repeat-customers/$', mobovidata_dj.ltv.views.repeat_customer_report,
        name='repeat-customer-report'),
]
