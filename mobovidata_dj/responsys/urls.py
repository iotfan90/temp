# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from .views import (BDaySubmission, EmailRIIDLookup, NpsSubmission, token_list,
                    UnsubForm)

urlpatterns = [
    url(regex=r'^token$', view=token_list, name='token_list'),
    url(r'^email-riid-lookup/$', EmailRIIDLookup.as_view(),
        name='email-riid-lookup'),
    url(r'^email-preferences/$', UnsubForm.as_view(), name='email-preferences'),
    url(r'^bday-submission/(?P<riid>[\w.%+-])/$', BDaySubmission.as_view(),
        name='bday-submission'),
    url(r'^bday-submission/$', BDaySubmission.as_view(),
        name='bday-submission'),
    url(r'^nps/$', NpsSubmission.as_view(), name='nps-submission'),
]
