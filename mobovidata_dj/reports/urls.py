# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

import mobovidata_dj.reports.views

urlpatterns = [
    url(r'^(?P<pk>\d+).csv$', mobovidata_dj.reports.views.export_csv,
        name='export_report_csv'),
]


