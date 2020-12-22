from django.contrib import admin
from .models import FacebookAd, OptimizeNotification, FacebookAPISettings


# Register your models here.
class FacebookAdAdmin(admin.ModelAdmin):
    list_display = [ x.name for x in FacebookAd._meta.get_fields() ]

# Register your models here.
class OptimizeNotificationAdmin(admin.ModelAdmin):
    list_display = [ x.name for x in OptimizeNotification._meta.get_fields() ]


class FacebookAPISettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'app_id', 'account_id', 'page_id',
                    'instagram_actor_id', 'version')
    search_fields = ('name',)

admin.site.register(OptimizeNotification, OptimizeNotificationAdmin)
admin.site.register(FacebookAPISettings, FacebookAPISettingsAdmin)
