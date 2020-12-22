from django.contrib import admin

from .models import EMAIL_MODELS

for model in EMAIL_MODELS:
    class DynamicAdmin(admin.ModelAdmin):
        list_display = model.__csv_fields__
    admin.site.register(model, DynamicAdmin)
