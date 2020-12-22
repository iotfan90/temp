from __future__ import unicode_literals

from django.apps import AppConfig


class ShopifyConfig(AppConfig):
    name = 'mobovidata_dj.shopify'

    def ready(self):
        super(ShopifyConfig, self).ready()

        import signals
