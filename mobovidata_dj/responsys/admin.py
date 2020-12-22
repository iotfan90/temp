from django.contrib import admin

# Register your models here.
from models import *


class ResponsysCredentialAdmin(admin.ModelAdmin):

    list_display = ('token', 'endpoint', 'modified_dt')
    actions = ['handle_responsys_token_update']

    def handle_responsys_token_update(self, request, queryset):
        from utils import get_responsys_token
        auth_token = get_responsys_token()
        try:
            obj = ResponsysCredential.objects.get()
            obj.token = auth_token['authToken']
            obj.endpoint = auth_token['endPoint']
            obj.save()
        except ResponsysCredential.DoesNotExist:
            obj = ResponsysCredential(
                token = auth_token['authToken'],
                endpoint = auth_token['endPoint']
            )
            obj.save()

admin.site.register(ResponsysCredential, ResponsysCredentialAdmin)
