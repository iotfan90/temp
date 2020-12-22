from django.contrib import admin

from models import *


class CustomerAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'riid', 'created_dt', 'modified_dt')
    search_fields = ('uuid', 'riid')


class CustomerSessionAdmin(admin.ModelAdmin):
    list_display = ('customer', 'session_id', 'num_page_views', 'modified_dt',
                    'created_dt')
    search_fields = ('customer', 'session_id',)


class CustomerPageViewAdmin(admin.ModelAdmin):
    list_display = ('session', 'url_path', 'product_fullid', 'created_dt',
                    'modified_dt')
    search_fields = ('session', 'url_path', 'product_fullid',)


class CustomerCartAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'session')
    search_fields = ('cart_id', 'session',)


class CustomerOrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'session', 'first_visit_url_path',
                    'first_visit_product_fullid', 'first_visit_url_parameters',
                    'first_visit_created_dt')
    search_fields = ('order_id', 'session', 'first_visit_url_path',
                     'first_visit_product_fullid', 'first_visit_url_parameters',
                     'first_visit_created_dt')


class CustomerLifecycleTrackingAdmin(admin.ModelAdmin):
    list_display = ('customer', 'funnel_step', 'lifecycle_messaging_stage',
                    'lifecycle_messaging_data', 'created_dt', 'modified_dt')
    search_fields = ('customer', 'funnel_step', 'lifecycle_messaging_stage',
                     'lifecycle_messaging_data', 'created_dt', 'modified_dt')
    actions = ['reset_funnel']

    def reset_funnel(self, request, queryset):
        queryset.update(funnel_step=-1)
    reset_funnel.short_description = "Reset funnel steps to post-order"


class CustomerStrandsIdAdmin(admin.ModelAdmin):
    list_display = ('customer', 'strands_id', 'created_dt', 'modified_dt')
    search_fields = ('customer', 'strands_id', 'created_dt', 'modified_dt')


class MobovidaCustomerEmailsAdmin(admin.ModelAdmin):
    list_display = ('email', 'email_md5', 'created_dt', 'modified_dt')
    search_fields = ('email', 'email_md5')

admin.site.register(Customer, CustomerAdmin)
admin.site.register(CustomerSession, CustomerSessionAdmin)
admin.site.register(CustomerPageView, CustomerPageViewAdmin)
admin.site.register(CustomerCart, CustomerCartAdmin)
admin.site.register(CustomerOrder, CustomerOrderAdmin)
admin.site.register(CustomerLifecycleTracking, CustomerLifecycleTrackingAdmin)
admin.site.register(CustomerStrandsId, CustomerStrandsIdAdmin)
admin.site.register(MobovidaCustomerEmails, MobovidaCustomerEmailsAdmin)
