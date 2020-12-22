from __future__ import absolute_import
import os
import pytz
import random

from celery import Celery
from datetime import datetime, timedelta
from django.apps import AppConfig
from django.conf import settings
from django.utils import timezone


if not settings.configured:
    # set the default Django settings module for the 'celery' program.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    # pragma: no cover


app = Celery('mobovidata_dj')


class CeleryConfig(AppConfig):
    name = 'mobovidata_dj.taskapp'
    verbose_name = 'Celery Config'

    def ready(self):
        # Using a string here means the worker will not have to
        # pickle the object when using Windows.
        app.config_from_object('django.conf:settings')
        app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, force=True)

        if hasattr(settings, 'RAVEN_CONFIG'):
            # Celery signal registration
            from raven import Client as RavenClient
            from raven.contrib.celery import register_signal as raven_register_signal
            from raven.contrib.celery import register_logger_signal as raven_register_logger_signal

            raven_client = RavenClient(dsn=settings.RAVEN_CONFIG['DSN'])
            raven_register_logger_signal(raven_client)
            raven_register_signal(raven_client)

        if hasattr(settings, 'OPBEAT'):
            from opbeat.contrib.django.models import client as opbeat_client
            from opbeat.contrib.django.models import logger as opbeat_logger
            from opbeat.contrib.django.models import register_handlers as opbeat_register_handlers
            from opbeat.contrib.celery import register_signal as opbeat_register_signal

            try:
                opbeat_register_signal(opbeat_client)
            except Exception as e:
                opbeat_logger.exception('Failed installing celery hook: %s' % e)

            if 'opbeat.contrib.django' in settings.INSTALLED_APPS:
                opbeat_register_handlers()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))  # pragma: no cover


@app.task()
def run_job_execution(exc_id):
    from mobovidata_dj.taskapp.models import JobExecution
    qs = JobExecution.objects.filter(pk=exc_id)
    exc = qs.get()

    if exc.status != 'pending' and not exc.started_at:
        return None
    else:
        qs.update(status='active', started_at=datetime.now(pytz.utc))

    try:
        result = exc.job.func()
        success = True
    except Exception as e:
        try:
            result = e.message
        except:
            result = str(e)
        success = False

    qs.update(status=(success and 'success' or 'error'), result=result,
              finished_at=datetime.now(pytz.utc))
    return result


@app.task()
def start_due_jobs():
    from mobovidata_dj.taskapp.models import JobSchedule, JobExecution
    from mobovidata_dj.taskapp.utils import get_active, get_reserved
    ALLOW = settings.JOB_WORKERS
    RUNNING = JobExecution.objects.filter(status__in=['active', 'pending'])
    DEAD_AGE = timezone.now() - timedelta(minutes=10)

    # Often, if we deploy while a task is running, we'll get left
    # with dangling entries in the Jobs table that cause
    # the workers queue to stop processing, so if something
    # is more than 10m old and it's not active, kill it
    old_jobs = RUNNING.filter(created_at__lte=DEAD_AGE)
    if old_jobs.count():
        valid_ids = get_active().keys() + get_reserved().keys()
        dead_jobs = [j for j in old_jobs if j.task_id not in valid_ids]
        if dead_jobs:
            print("Found dead jobs, invalidating: %s" % dead_jobs)
            for j in dead_jobs:
                j.status = 'disappeared'
                j.save()

    due_jobs = [schedule.job for schedule in
                    JobSchedule.objects.filter(status='active')
                    if schedule.is_due() and schedule.job.allow_trigger()]
    print("Due jobs: %s" % due_jobs)
    if not due_jobs:
        return
    START = (ALLOW - RUNNING.count())
    print("Allowed: %s Running: %s Starting: %s" % (ALLOW, RUNNING.count(),
                                                    START))

    for n in xrange(0, START):
        need_running = [j for j in due_jobs if
                        j.limit >= j.get_running().count()
                        and j.allow_trigger()]
        if not need_running:
            return
        print("Triggering: %s" % j)
        job = random.choice(need_running)
        job.trigger()
