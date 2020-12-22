import json

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin

from .utils import get_image_gallery
from modjento.models import EavAttribute


class ImageCreator(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'creator.html'
    login_url = '/accounts/login'

    def __init__(self):
        super(ImageCreator, self).__init__()

    def get(self, request, *args, **kwargs):
        return self.render_to_response(context={})


class ImageView(LoginRequiredMixin, TemplateResponseMixin, View):
    template_name = 'view.html'
    login_url = '/account/login'

    def __init__(self):
        super(ImageView, self).__init__()

    def post(self, request, *args, **kwargs):
        product_ids = [x.strip() for x in request.POST.getlist('products[]')]
        product_ids = filter(None, product_ids)
        rg_fields = ['name', 'image', 'price', 'special_price', 'msrp',
                     'url_path', 'url_key']
        rg_products = []
        mp_values = EavAttribute.objects.get_values(
            product_ids,
            entity_type=4,
            field_names=rg_fields,
            json_values=False)
        mp_gallery = get_image_gallery(rg_product_ids=product_ids)
        for product_id in product_ids:
            product_id = int(product_id)
            p_attr = mp_values.get(product_id)
            if not p_attr:
                continue
            product = {'product_id': product_id}
            for field in p_attr:
                product[field] = p_attr.get(
                    field) if field not in ['msrp', 'price',
                                            'special_price'] else round(
                    p_attr.get(field), 2)
            product['co_price'] = product.get('special_price') or product.get(
                'price')
            product['images'] = mp_gallery.get(product_id)
            product['url_path'] = settings.MAGENTO_URL_PREFIXES[
                                      'pdp'] + product.get('url_path')
            image = settings.MAGENTO_URL_PREFIXES['img'] + product.get('image')
            if image not in product['images']:
                product['images'].append(
                    settings.MAGENTO_URL_PREFIXES['img'] + product.get('image'))
            rg_products.append(product)
        return self.render_to_response(context={
            'products': json.dumps(rg_products)
        })
