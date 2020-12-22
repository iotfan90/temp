from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import ReportQuery, ReportExecution


def export_csv_to_s3(modeladmin, request, queryset):
    for obj in queryset.all():
        obj.delay_execute('s3', 'csv')


def export_csv_to_redshift(modeladmin, request, queryset):
    for obj in queryset.all():
        obj.delay_execute('redshift', 'csv', gzip=True)


class ReportQueryAdmin(admin.ModelAdmin):

    def get_link(self, obj):
        return mark_safe('<a href="%s">Click here</a>'%obj.csv_url)
    list_display = ['created_at', 'modified_at', 'title', 'source', 'query',
                    'get_link']
    actions = [export_csv_to_s3, export_csv_to_redshift]


class ReportExecutionAdmin(admin.ModelAdmin):

    def query_name(self, obj):
        return obj.query.title
    list_display = ['created_at', 'query_name', 'started_at', 'completed_at',
                    'status', 'message', 'target', 'format']

admin.site.register(ReportQuery, ReportQueryAdmin)
admin.site.register(ReportExecution, ReportExecutionAdmin)
