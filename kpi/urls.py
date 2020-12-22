from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from kpi import views as kpi_views


urlpatterns = [
    url(r'^hourly-sales-tracker/', kpi_views.HourlySalesTracker.as_view(),
        name='hourly-sales-tracker'),
    url(r'^daily-sales-tracker/', kpi_views.DailySalesTracker.as_view(),
        name='daily-sales-tracker'),
    url(r'^monthly-sales-tracker/', kpi_views.MonthlySalesTracker.as_view(),
        name='monthly-sales-tracker'),
]
