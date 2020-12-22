# -*- coding: utf-8 -*-
from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .taskapp import celery_app as celery

__all__ = ['celery']

__version__ = '0.0.1'
__version_info__ = tuple([int(num) if num.isdigit() else num for num in __version__.replace('-', '.', 1).split('.')])
