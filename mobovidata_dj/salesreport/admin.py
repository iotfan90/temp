from django.contrib import admin

from models import DailyAvgWeights


@admin.register(DailyAvgWeights)
class DailyAvgWeightsAdmin(admin.ModelAdmin):
    list_display = ('day_1', 'day_3', 'day_7', 'day_14', 'day_30', 'day_90')
