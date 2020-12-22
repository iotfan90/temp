import importlib
import pytz

from datetime import datetime, timedelta
from django.db import models

from .utils import time_in_range

"""
Celery Jobs -- For Long-running background task execution and rate limiting
To use it:
    + Ensure settings.JOB_WORKERS >= 1
    + Define a method "process_xyz_batch()"
     -- Takes no arguments, processes a batch of the data
     -- Runs up to ~5-10 minutes (or more is OK, but not much less)
     -- Optionally/preferably no race conditions, concurrency-friendly
     -- Optionally, set a "predicate" attribute that is a callable
     -- The job won't run if the predicate evaluates to False
        (e.g. process_xyz.predicate = lambda: more_entries_available() )

    + Create a JobDefinition entry for this method, limit its concurrency
    + Create a JobSchedule entry for this Definition
    + Now it will automatically keep itself running in rotation
    + The method taskapp.celery_app.start_due_jobs will check every 30s for
        available workers and fill them with jobs
"""

JOB_STATUS = [
    ('pending', 'Pending'),
    ('active', 'Active'),
    ('error', 'Error'),
    ('disappeared', 'Disappeared'),
    ('success', 'Success'),
]


class JobExecution(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=1024, null=True, blank=True)
    job = models.ForeignKey('JobDefinition', null=True, blank=True,
                            related_name='executions')
    status = models.CharField(max_length=32, choices=JOB_STATUS,
                              default='pending')
    task_id = models.CharField(max_length=1024, null=True, blank=True,
                               db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    instance_number = models.PositiveIntegerField(null=True, blank=True)
    result = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '[%s] %s' % (self.status, self.job)

    @property
    def duration(self):
        return self.started_at and self.finished_at and (self.finished_at -
                                     self.started_at).total_seconds() or 0
    @property
    def delayed(self):
        return self.started_at and (self.started_at -
                                     self.created_at).total_seconds() or 0

    @property
    def age(self):
        return datetime.now(pytz.utc) - self.created_at

    class Meta:
        ordering = ('-created_at',)


class JobDefinition(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=1024, null=True, blank=True)
    method = models.CharField(max_length=1024, null=True, blank=True)
    limit = models.PositiveIntegerField('Concurrent limit', null=True,
                                        blank=True, default=0)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return self.title or self.method

    @property
    def duration(self):
        return self.started_at and self.finished_at and (self.finished_at -
                                     self.started_at).total_seconds() or 0
    @property
    def delayed(self):
        return self.started_at and (self.started_at -
                                     self.created_at).total_seconds() or 0

    @property
    def func(self):
        mod_name, func_name = self.method.rsplit('.', 1)
        mod = importlib.import_module(mod_name)
        return getattr(mod, func_name)

    @classmethod
    def get_method(cls, method, or_create=True):
        try: definition = cls.objects.get(method=method)
        except cls.DoesNotExist:
            if not or_create: return None
            else: definition = cls.objects.create(method=method, limit=1)

        return definition

    def allow_trigger(self):
        if callable(getattr(self.func, 'predicate', None)):
            if not self.func.predicate():
                return False
        return True

    def trigger(self):
        from mobovidata_dj.taskapp.celery_app import app, run_job_execution
        if not self.allow_trigger(): return False
        title = self.method
        this_num = None
        if self.limit:
            pending = self.executions.filter(
                    status__in=['active', 'pending'])

            if pending.count() >= self.limit:
                exc = pending.first()
                task = app.AsyncResult(exc.task_id)
                if not task:
                    run_job_execution.delay(exc.id)
                return pending.first()

            instances = [p.instance_number for p in pending]
            this_num = 1
            for i in range(1,self.limit+1):
                if i not in instances:
                    this_num = i
                    break
            if this_num == 1 and self.limit == 1:
                title = '%s {singleton}'%title
            else:
                title = '%s {%s/%s}'%(title, this_num, self.limit)

        exc = self.executions.create(
            title=title,
            instance_number = this_num,
        )

        task = run_job_execution.delay(exc.id)

        exc.task_id = task.id
        exc.save()
        return exc

    def get_running(self):
        return self.executions.filter(status__in=['active', 'paused'])

    def last_execution(self):
        try: return self.executions.all()[0]
        except IndexError: return None

    class Meta:
        ordering = ('-created_at',)


UNIT_CHOICES = [(1, 'seconds'), (60, 'minutes'), (3600, 'hours'),
                (86400, 'days')]
SCHEDULE_STATUS_CHOICES = [('paused', 'Pause'), ('active', 'Active')]


class JobSchedule(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    job = models.ForeignKey(JobDefinition, related_name='schedules')
    status = models.CharField(max_length=16, default='paused',
                              choices=SCHEDULE_STATUS_CHOICES)
    interval = models.PositiveIntegerField()
    unit = models.PositiveIntegerField(choices=UNIT_CHOICES, default=1)
    time = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '[%s] %s every %s %s'%(self.status, self.job, self.interval,
                                      self.get_unit_display())

    @property
    def interval_seconds(self):
        return self.interval * self.unit

    def is_time_in_range(self):
        if not self.time:
            return True
        start = datetime.now() - timedelta(minutes=30)
        end = datetime.now() + timedelta(minutes=30)
        return time_in_range(start.time(), end.time(), self.time)

    def is_due(self):
        paused = self.status == 'paused'
        last = self.job.last_execution()

        is_due = ((not paused) and
                  ((not last) or
                   ((last.age.total_seconds() >= self.interval_seconds) and self.is_time_in_range())))
        print "Is Due? %s -> %s (%s >= %s)"%(is_due, self,
                                             last and last.age.total_seconds(),
                                             self.interval_seconds)
        return is_due

    class Meta:
        ordering = ('-created_at',)

BACKUP_STATUS_CHOICES = [('running', 'Running'), ('success', 'Success'),
                         ('error', 'Error')]


class BackupLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, default='running',
                              choices=BACKUP_STATUS_CHOICES)
    output = models.TextField(null=True, blank=True)
