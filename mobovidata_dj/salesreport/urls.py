# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from .views import (InventoryQuarantine, mobovida_sales, PurchaseOrderReport,
                    PurchaseOrderReportCsvExport, SalesReport,
                    SalesReportCsvExport)

urlpatterns = [
    url(r'^salesreport/$', SalesReport.as_view(), name='sales-report'),
    url(r'^poreport/$', PurchaseOrderReport.as_view(), name='po-report'),
    url(r'^salesreport/csv/$', SalesReportCsvExport.as_view(),
        name='sales-report-csv-export'),
    url(r'^poreport/csv/$', PurchaseOrderReportCsvExport.as_view(),
        name='po-report-csv-export'),
    url(r'^mobovida-sales/$', mobovida_sales, name='mobovida-sales-report'),
    url(r'^inventory-quarantine/$', InventoryQuarantine.as_view(),
        name='inventory-quarantine'),
]
