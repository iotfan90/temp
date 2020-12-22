from django.conf import settings
from django_assets import Bundle, register


settings.ASSETS_AUTO_BUILD = True
settings.ASSETS_DEBUG = 'merge'
vendor_css = Bundle(
    'vendor/bootstrap/dist/css/bootstrap.min.css',
    'vendor/font-awesome/css/font-awesome.min.css',
    'vendor/slick-carousel/slick/slick.css',
    'vendor/slick-carousel/slick/slick-theme.css',
    'vendor/angular-chart.js/dist/angular-chart.min.css',
    filters='cssrewrite',
    output='compiled/vendor.css'
)
register('vendor_css', vendor_css)

vendor_js = Bundle(
    'vendor/jquery/dist/jquery.min.js',
    'vendor/angular/angular.min.js',
    'vendor/tether/dist/js/tether.min.js',
    'vendor/bootstrap/dist/js/bootstrap.min.js',
    'vendor/html5shiv/dist/html5shiv.min.js',
    'vendor/trianglify/dist/trianglify.min.js',
    'vendor/slick-carousel/slick/slick.min.js',
    'vendor/Chart.js/Chart.js',
    'vendor/angular-chart.js/dist/angular-chart.min.js',
    filters='rjsmin',
    output='compiled/vendor.js'
)
register('vendor_js', vendor_js)


modjento_css = Bundle(
    'scss/modjento.scss',
    filters='pyscss,cssmin',
    output='compiled/modjento.min.css')

register('modjento_css', modjento_css)


modjento_js = Bundle(
    'app/base.js',
    'app/inventory_supplier_mapping_update.js',
    'app/facebook_preview.js',
    'app/ad_creator.js',
    'app/shopify_ad_creator.js',
    'app/shopify_ad_preview.js',
    'app/multiple_ad_creator.js',
    'app/multiple_ad_preview.js',
    'app/lifecycle_campaigns.js',
    'app/campaign_logs.js',
    'app/email_from_riid.js',
    'app/salesorder.js',
    'app/poreport.js',
    'app/fb_login.js',
    'app/kpi.js',
    'app/fb_login.js',
    'app/email_sign_up_track.js',
    'app/customer_dashboard.js',
    'app/customer_email.js',
    'app/lifecycle_analytics.js',
    'app/unsub_form.js',
    'app/order_lookup.js',
    'app/order_details.js',
    'app/product_review.js',
    'app/review_submit.js',
    'app/bday_submission.js',
    'app/bday_after_sub.js',
    'app/inventory_quarantine.js',
    'app/image_retrieval_view.js',
    'app/product_bulk_association.js',
    'app/product_bulk_create.js',
    'app/product_bulk_update.js',
    'app/variant_update.js',
    'app/product_feed_exclusion_update.js',
    'app/smart_collection_sync_preview.js',
    'app/model_bulk_update.js',
    'app/shopify_more_actions.js',
    'app/webhook.js',
    filters='rjsmin',
    output='compiled/modjento.js'
)
register('modjento_js', modjento_js)
