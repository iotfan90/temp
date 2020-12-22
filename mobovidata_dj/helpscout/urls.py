# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

import mobovidata_dj.helpscout.views

urlpatterns = [
    url(r'^email-list/$',
        mobovidata_dj.helpscout.views.HelpScoutEmails.as_view(),
        name='email-list'),
]
