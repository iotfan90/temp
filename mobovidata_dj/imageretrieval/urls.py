# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from mobovidata_dj.imageretrieval import views

urlpatterns = [
    url(r'^creator/$', views.ImageCreator.as_view(), name='creator'),
    url(r'^view/$', views.ImageView.as_view(), name='view'),
]
