from __future__ import unicode_literals
from enum import Enum


class Visibility(Enum):
    not_visible = 2
    visible = 1


class EntityType(Enum):
    """
    Quick and useful Enum for queries to the EavAttribute table.
    You can get the full list of entity type IDs by querying
    eav_entity_type
    """
    customer = 1
    address = 2
    category = 3
    product = 4
    order = 5
    invoice = 6
    credit_memo = 7
    shipment = 8


class ReviewEntity(Enum):
    product = 1
    customer = 2
    category = 3


class ReviewStatus(Enum):
    approved = 1
    pending = 2
    not_approved = 3


class EavAttributes(Enum):
    image = 79
    small_image = 80
    thumbnail = 81
    name = 65
    visibility = 96
    status = 89
    url_key = 90
    url_path = 91


class ProductAttributes(object):
    image = 79
    small_image = 80
    thumbnail = 81
    name = 65
    visibility = 95
    status = 89
    url_key = 90
    url_path = 91


class ProductStatus(Enum):
    enabled = 1
    disabled = 2


class ProductFields(object):
    image = 'image'
    small_image = 'small_image'
    thumbnail = 'thumbnail'
    images = 'images'
    url = 'url'
    alt_text = 'alt_text'
