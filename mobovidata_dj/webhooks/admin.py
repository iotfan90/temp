from django.contrib import admin

from .models import Dojomojo, Unbounce, WebhookTransaction


class DojomojoAdmin(admin.ModelAdmin):
    list_display = ('campaign_name', 'fullname', 'email', 'referrer', 'source',
                    'state', 'status')
    search_fields = ('campaignname', 'fullname', 'firstname', 'lastname',
                     'email', 'gender', 'phone', 'birthday', 'referrer',
                     'source', 'ip', '', 'street_address', 'city', 'state',
                     'zipcode', 'custom_field')
    list_filter = ('status',)


class UnbounceAdmin(admin.ModelAdmin):
    list_display = ('email_address', 'page_name', 'page_url', 'date_submitted',
                    'time_submitted', 'variant', 'date_processed', 'status')
    search_fields = ('email_address', 'page_name', 'page_url', 'date_submitted',
                     'time_submitted')
    list_filter = ('date_submitted', 'time_submitted', 'date_processed',
                   'status', 'variant')


class WebhookTransactionAdmin(admin.ModelAdmin):
    list_display = ('webhook_type', 'date_received', 'date_processed', 'status')
    search_fields = ('date_received', 'date_processed')
    list_filter = ('webhook_type', 'status', 'date_received', 'date_processed')


admin.site.register(Dojomojo, DojomojoAdmin)
admin.site.register(Unbounce, UnbounceAdmin)
admin.site.register(WebhookTransaction, WebhookTransactionAdmin)
