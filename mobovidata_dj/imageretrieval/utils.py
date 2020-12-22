import logging

from collections import defaultdict
from django.conf import settings

from modjento.models import CatalogProductEntityMediaGalleryValue

logger = logging.getLogger(__name__)


def get_image_gallery(rg_product_ids):
    rg_image_data = (CatalogProductEntityMediaGalleryValue.objects
                     .select_related('value')
                     .filter(value__entity_id__in=rg_product_ids,
                             disabled=False)
                     .order_by('position')
                     .values_list('value__entity_id', 'value__value'))

    mp_images = defaultdict(list)
    for n_id, value in rg_image_data:
        st_image = settings.MAGENTO_URL_PREFIXES['img'] + value
        mp_images[n_id].append(st_image)
    return mp_images
