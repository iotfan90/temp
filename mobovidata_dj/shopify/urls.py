from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from .views import (BrandsModelsJS, BrandsModelImagesJS, DiscountCodeRedeem,
                    InventorySupplierMappingBulkUpdate, ModelBulkUpdate,
                    MoreActions, MoreActionsGenerateWEProductFeeds,
                    MoreActionsSyncOrders, MoreActionsSyncProducts,
                    MoreActionsSyncSmartCollections,
                    MoreActionsUpdateModelsToShopify,
                    MoreActionsUploadBrandModelsJSFile, NewModelUploadShopify,
                    NewModelsUploadShopifyPreview,
                    NewModelsUploadShopifyStoreSelector,
                    ProductBulkAssociation, ProductBulkCreate,
                    ProductBulkUpdate, ProductFeedExclusionUpdate,
                    ProductFeedList, VariantUpdate, WebhookCreate,
                    WebhookDelete, WebhookStoreSelector, Generate_co_product_feeds, Show_test_message)

urlpatterns = [
    url(r'^brand_models.js$', BrandsModelsJS.as_view()),
    url(r'^brand_model_images.js$', BrandsModelImagesJS.as_view()),
    url(r'^discount_code/$', DiscountCodeRedeem.as_view()),

    url(r'^inventory_supplier_mapping/bulk_update/$',
        InventorySupplierMappingBulkUpdate.as_view(),
        name='update-inventory-supplier-mapping-bulk'),

    url(r'^model/bulk_update/$', ModelBulkUpdate.as_view(),
        name='update-model-bulk'),
    url(r'^model/upload/$', NewModelUploadShopify.as_view(),
        name='upload-new-model-to-shopify'),
    url(r'^model/upload/preview/$', NewModelsUploadShopifyPreview.as_view(),
        name='upload-new-models-to-shopify-preview'),
    url(r'^model/upload/store_selector$',
        NewModelsUploadShopifyStoreSelector.as_view(),
        name='upload-new-models-to-shopify-store-selector'),

    url(r'^more_actions/$', MoreActions.as_view(), name='more-actions'),
    url(r'^more_actions/generate-we-product-feeds/$',
        MoreActionsGenerateWEProductFeeds.as_view(),
        name='more-actions-we-product-feed-generation'),
    url(r'^more_actions/sync-products/$', MoreActionsSyncProducts.as_view(),
        name='more-actions-sync-products'),
    url(r'^more_actions/sync-smart-collections/$',
        MoreActionsSyncSmartCollections.as_view(),
        name='more-actions-sync-smart-collections'),
    url(r'^more_actions/sync-orders/$', MoreActionsSyncOrders.as_view(),
        name='more-actions-sync-orders'),
    url(r'^more_actions/update-models-to-shopify/$',
        MoreActionsUpdateModelsToShopify.as_view(),
        name='more-actions-update-models-to-shopify'),
    url(r'^more_actions/upload-brand-model-js/$',
        MoreActionsUploadBrandModelsJSFile.as_view(),
        name='more-actions-upload-brand-model-js'),

    url(r'^product/bulk_association/', ProductBulkAssociation.as_view(),
        name='bulk-associate-product'),
    url(r'^product/bulk_create/', ProductBulkCreate.as_view(),
        name='bulk-create-product'),
    url(r'^product/bulk_update/', ProductBulkUpdate.as_view(),
        name='bulk-update-product'),

    url(r'^product_feed/exclusion/update$', ProductFeedExclusionUpdate.as_view(),
        name='product-feed-exclusion-update'),
    url(r'^product_feed/list$', ProductFeedList.as_view(),
        name='product-feed-list'),

    url(r'^variant/update/', VariantUpdate.as_view(), name='update-variant'),
    url(r'^show_test_message', Show_test_message.as_view(), name='show-test-message'),

    url(r'^generate_co_product_feeds', Generate_co_product_feeds.as_view(), name='generate-co-product-feeds'),

    url(r'^webhook/create', WebhookCreate.as_view(), name='webhook-create'),
    url(r'^webhook/delete', WebhookDelete.as_view(), name='webhook-delete'),
    url(r'^webhook/list/store_selector', WebhookStoreSelector.as_view(),
        name='webhook-store-selector'),
]
