import os

from django.contrib import admin

from .models import CSVImport, CSVImportError


class CSVImportAdmin(admin.ModelAdmin):
    def success_rate(self, obj):
        return obj.get_success_rate()

    def file_exists_on_disk(self, obj):
        return os.path.exists(obj.filename)

    list_display = ['discovered_at', 'target_type', 'parsed_at',
                    'status', 'success_rate', 'expected_rows', 'parsed_rows',
                    'filename', 'file_exists_on_disk']


class CSVImportErrorAdmin(admin.ModelAdmin):
    list_display = ['csv', 'row', 'error', 'data']


admin.site.register(CSVImport, CSVImportAdmin)
admin.site.register(CSVImportError, CSVImportErrorAdmin)
