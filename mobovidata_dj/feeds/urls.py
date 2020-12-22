# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^generate-feeds/$',
        view=views.generate_feeds,
        name='generate_feeds'
    ),
]
