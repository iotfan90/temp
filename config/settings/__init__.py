# -*- coding: utf-8 -*-
from __future__ import absolute_import

import __builtin__
import sys
from .common import *
try:
    from . import environment
    env = environment.ENVIRONMENT
except ImportError:
    env = 'development'

env_name = os.environ.get('MOBOVIDATA_RUNTIME_ENVIRONMENT', env)


if env_name == 'staging':
    env_name = 'production'
__imported_module = __builtin__.__import__('%s' % env_name, globals(), locals(), ['*'], -1)
locals().update(__imported_module.__dict__)

if 'test' in sys.argv or 'test_coverage' in sys.argv:
    from .test_settings import *

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from mobovidata_dj.taskapp import celery_app


__all__ = ['celery_app']
