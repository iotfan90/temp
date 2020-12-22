from django.contrib import admin

from models import SalesFlatQuote


class SalesFlatQuoteAdmin(admin.ModelAdmin):

    list_display = ('entity_id', 'created_at', 'is_active', 'items_count')
    search_fields = ('entity_id', 'created_at', 'is_active', 'items_count')

admin.site.register(SalesFlatQuote, SalesFlatQuoteAdmin)
