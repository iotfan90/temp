from datetime import timedelta
from django.contrib import admin

from .models import BackupLog, JobDefinition, JobExecution, JobSchedule
from .utils import get_active_cached, get_reserved_cached, get_scheduled_cached


class JobExecutionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'status', 'job',
                    'instance_number', 'started_at', 'finished_at', 'duration',
                    'delayed', 'task_id', 'task_status')
    search_fields = ('created_at', 'job', 'instance_number', 'started_at',
                     'finished_at', 'task_id')
    list_filter = ('status', 'created_at', 'started_at', 'finished_at', 'job')

    def duration(self, obj):
        return str(timedelta(seconds=int(obj.duration)))

    def delayed(self, obj):
        return str(timedelta(seconds=int(obj.delayed)))

    def task_status(self, obj):
        if obj.status == 'success':
            return 'SUCCESS'
        if obj.status == 'error':
            return 'ERROR'
        active = get_active_cached()
        if obj.task_id in active:
            return 'ACTIVE - %s'%active[obj.task_id]
        reserved = get_reserved_cached()
        if obj.task_id in reserved:
            return 'RESERVED - %s'%reserved[obj.task_id]
        scheduled = get_scheduled_cached()
        if obj.task_id in scheduled:
            return 'SCHEDULED - %s'%scheduled[obj.task_id]
        return 'UNKNOWN'


class JobDefinitionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'title', 'method', 'limit')
    search_fields = ('title', 'method',)
    list_filter = ('limit', 'created_at')


class JobScheduleAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'job', 'interval', 'unit', 'status')
    search_fields = ('created_at', 'job',)
    list_filter = ('status', 'interval', 'unit', 'created_at')


class BackupLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'finished_at', 'status', 'output')
    search_fields = ('created_at', 'finished_at', 'output')
    list_filter = ('status', 'created_at', 'finished_at')


admin.site.register(BackupLog, BackupLogAdmin)
admin.site.register(JobDefinition, JobDefinitionAdmin)
admin.site.register(JobExecution, JobExecutionAdmin)
admin.site.register(JobSchedule, JobScheduleAdmin)
