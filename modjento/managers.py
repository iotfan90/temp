# encoding: utf-8
import copy
import logging

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from django.db import models

from modjento.enums import EavAttributes, EntityType, ProductStatus, Visibility

logger = logging.getLogger(__name__)


class EavOptionManager(models.Manager):
    def get_cached_ids(self):
        ms_ids = getattr(self, 'ms_ids', None)
        if ms_ids is not None:
            return ms_ids
        ms_ids = set(self.values_list('attribute_id', flat=True))
        setattr(self, 'ms_ids', ms_ids)
        return ms_ids

    def has_options(self, n_id):
        return n_id in self.get_cached_ids()


class EavOptionValueManager(models.Manager):
    def get_cached_values(self):
        mp_values = getattr(self, 'mp_values', None)
        if mp_values is not None:
            return mp_values
        mp_values = dict(self.values_list('option_id', 'value'))
        setattr(self, 'mp_values', mp_values)
        return mp_values

    def lookup(self, st_ids):
        if isinstance(st_ids, basestring):
            rg_ids = map(int, st_ids.split(','))
        else:
            rg_ids = [st_ids]
        rg_boomerang = []
        rg_values = []
        for x in rg_ids:
            value = self.get_cached_values().get(x)
            if value:
                rg_values.append(value)
                rg_boomerang.append({
                    'index': x,
                    'value': value,
                })

        return rg_ids, ','.join(rg_values), rg_boomerang


class EavAttributeManager(models.Manager):
    def attributes_by_model(
            self,
            entity_type=4,
            field_names=None):
        """
        The function returns all EAV attributes associated with
        the product entity in Magento (entity_type_id=4).  The
        returned attributes are organized and sorted as follows:
          backend_type -> attribute_id -> attribute_code
        The above organization makes it easier to query for the
        different EAV attribute values for export as part of the
        product feed.
        @return: dict[ str | unicode, dict[ long, str | unicode]]
        """
        # from magento.models import ProductFlat

        STATIC = 'static'
        qs_attributes = self.filter(
            entity_type_id=entity_type,
        )
        if field_names:
            qs_attributes = qs_attributes.filter(attribute_code__in=field_names)
        # If an attribute model is static, this means it is
        # stored as a column on the CatalogProductEntity table,
        # so need to retrieve it from the model backend
        # hierarchical tables.
        qs_attributes = qs_attributes.exclude(backend_type=STATIC)
        rg_attributes = list(qs_attributes.order_by('backend_type'))
        mp_attributes = defaultdict(dict)
        for x in rg_attributes:
            mp_attributes[x.backend_type][x.attribute_id] = x
        return mp_attributes

    def get_values(
                self,
                entity_ids,
                entity_type=4,
                field_names=None,
                option_indexes=False,
                chunk_size=500,
                convert_multiselects=False,
                boomerangs=False,
                date_format=None,
                datetime_format=None,
                json_values=True,
                store_id=2):
        """
        For a given set of product IDs, returns a dictonary where each
        product_id is associated with a map of attribute codes and values
        :param entity_ids: A list of the IDs whose field values the caller
                           wants to retrieve
        :type entity_ids: list[long]
        :param entity_type: An EntityType enum that specifies the type of
                            entity for which we want to retrieve EAV
                            value pairs
        :type entity_type: EntityType
        :param field_names: A caller can use this parameter to limit the fields
                           that are returned in the resulting list of
                           dictionaries
        :type field_names: list[unicode]
        :param chunk_size: Retrieving the values from the EAV structure can
                           be a long process, so in order not to overload
                           the database with requests that can will require
                           100s of MB of data in a response, a caller can
                           specify a chunk_size that will specify the maximum
                           number of entities for which to load EAV value pairs
                           at once.
        :type chunk_size long
        :return: dict[int, dict[unicode, object]]
        """
        from modjento.models import (CatalogProductEntityDatetime,
                                     CatalogProductEntityDecimal,
                                     CatalogProductEntityInt,
                                     CatalogProductEntityText,
                                     CatalogProductEntityVarchar,
                                     CatalogCategoryEntityDatetime,
                                     CatalogCategoryEntityDecimal,
                                     CatalogCategoryEntityInt,
                                     CatalogCategoryEntityText,
                                     CatalogCategoryEntityVarchar,
                                     CustomerEntityDatetime,
                                     CustomerEntityDecimal,
                                     CustomerEntityInt,
                                     CustomerEntityText,
                                     CustomerEntityVarchar,
                                     CustomerAddressEntityDatetime,
                                     CustomerAddressEntityDecimal,
                                     CustomerAddressEntityInt,
                                     CustomerAddressEntityText,
                                     CustomerAddressEntityVarchar,
                                     EavAttributeOption,
                                     EavAttributeOptionValue)
        mp_values = defaultdict(dict)
        mp_attributes = self.attributes_by_model(
            entity_type,
            field_names
        )
        rg_store_ids = [0, store_id]

        # rg_chunks = chunk_ids(entity_ids, chunk_size)
        MODEL_MAPS = {
            4: {
                'int': CatalogProductEntityInt,
                'varchar': CatalogProductEntityVarchar,
                'datetime': CatalogProductEntityDatetime,
                'decimal': CatalogProductEntityDecimal,
                'text': CatalogProductEntityText,
            },
            3: {
                'int': CatalogCategoryEntityInt,
                'varchar': CatalogCategoryEntityVarchar,
                'datetime': CatalogCategoryEntityDatetime,
                'decimal': CatalogCategoryEntityDecimal,
                'text': CatalogCategoryEntityText,
            },
            1: {
                'int': CustomerEntityInt,
                'varchar': CustomerEntityVarchar,
                'datetime': CustomerEntityDatetime,
                'decimal': CustomerEntityDecimal,
                'text': CustomerEntityText,
            },
            2: {
                'int': CustomerAddressEntityInt,
                'varchar': CustomerAddressEntityVarchar,
                'datetime': CustomerAddressEntityDatetime,
                'decimal': CustomerAddressEntityDecimal,
                'text': CustomerAddressEntityText,
            },
        }
        datetime_format = datetime_format or date_format
        mp_models = MODEL_MAPS.get(entity_type, None)
        if not mp_models:
            return {}

        for st_model, mp_attributes in mp_attributes.iteritems():
            value_model = mp_models.get(st_model)
            rg_ids = list(mp_attributes.iterkeys())
            print 'Loading %s values' % st_model
            if not value_model:
                continue
            # for chunk in rg_chunks:
            rg_values = value_model.objects.filter(
                entity_id__in=entity_ids,
                attribute_id__in=rg_ids,
                value__isnull=False,
                store_id__in=rg_store_ids,
            ).order_by(
                'entity_id', 'attribute_id', 'store_id'
            ).values_list('entity_id', 'attribute_id', 'value')
            for n_id, n_attribute_id, value in rg_values:
                p_attribute = mp_attributes.get(n_attribute_id)
                if not p_attribute:
                    continue
                st_code = p_attribute.attribute_code
                if value and EavAttributeOption.objects.has_options(n_attribute_id):
                    rg_indexes, value, rg_boomerang = (EavAttributeOptionValue
                                                       .objects.lookup(value))
                    if option_indexes:
                        mp_values[n_id]['_' + st_code] = rg_indexes
                    if boomerangs:
                        mp_values[n_id]['d' + st_code] = rg_boomerang
                    elif (p_attribute.frontend_input == 'multiselect' and
                              convert_multiselects):
                        value = [st for st in value.split(',') if st]
                elif value:
                    if isinstance(value, Decimal) and json_values:
                        value = float(value)
                    elif isinstance(value, datetime) and json_values:
                        if datetime_format:
                            value = value.strftime(datetime_format)
                        else:
                            value = value.isoformat()
                    elif isinstance(value, date) and json_values:
                        if date_format:
                            value = value.strftime(date_format)
                        else:
                            value = value.isoformat()
                mp_values[n_id][st_code] = value
            print 'Loaded %s values' % st_model
        return mp_values

    def get_bmc_link(self, bmc_id=None):
        """
        get the brand model category given the category id
        For seo purposes, we want to have the phone brand and phone model
        with the category id we can add the brand information to the product url
        :param bmc_id: brand model category id
        :return: product url
        """
        if not bmc_id:
            return ''
        if isinstance(bmc_id, str):
            bmc_id = int(bmc_id)
        bmc_link = self.get_values(
            entity_ids=[bmc_id],
            entity_type=3,
            field_names=['url_path'],
            json_values=False,
            store_id=2)
        return bmc_link[bmc_id]['url_path'].replace('.html', '')


class ProductManager(models.Manager):
    def get_sku_map(self):
        """
        Returns a mapping of all SKUs to the product ID
        @return: dict[ unicode ] => long
        """
        mp_skus = getattr(self, 'mp_skus', None)
        if mp_skus is not None:
            return mp_skus
        mp_skus = dict(self.values_list('sku', 'entity_id'))
        setattr(self, 'mp_skus', mp_skus)
        return mp_skus

    def get_parent_map(self):
        from modjento.models import CatalogProductEntityVarchar
        mp_parent = getattr(self, 'mp_parent', None)
        if mp_parent is not None:
            return mp_parent
        PARENT_SKU_ATTRIBUTE_ID = 869
        mp_parent_skus = dict(CatalogProductEntityVarchar.objects.filter(
            attribute_id=PARENT_SKU_ATTRIBUTE_ID
        ).values_list('entity_id', 'value'))
        mp_skus = self.get_sku_map()
        mp_parent = {
            key: mp_skus.get(value)
            for key, value in mp_parent_skus.iteritems()
        }
        setattr(self, 'mp_parent', mp_parent)
        return mp_parent

    def get_in_stock(self):
        from modjento.models import CataloginventoryStockItem
        from modjento.models import CatalogProductEntityInt
        ms_ids = set(CataloginventoryStockItem.objects.get_products_in_stock())
        mp_parents = self.get_parent_map()
        ms_temp = { mp_parents.get(x) for x in ms_ids }
        ms_ids |= ms_temp
        rg_enabled_ids = CatalogProductEntityInt.objects.filter(
            attribute_id=EavAttributes.status.value,
            entity_id__in=ms_ids,
            value=ProductStatus.enabled.value,
        ).values_list('entity_id', flat=True)
        ms_ids &= set(rg_enabled_ids)
        rg_ids = list(ms_ids)
        rg_ids.sort()
        return rg_ids

    def get_visible_ids(self):
        from modjento.models import CatalogProductEntityInt
        rg_visible_ids = CatalogProductEntityInt.objects.filter(
            attribute_id=EavAttributes.visibility.value
        ).exclude(
            value=Visibility.not_visible.value
        ).values_list('entity_id', flat=True)
        return list(rg_visible_ids)

    def get_enabled_ids(self):
        from modjento.models import CatalogProductEntityInt
        rg_enabled_ids = CatalogProductEntityInt.objects.filter(
            attribute_id=EavAttributes.status.value,
            value=ProductStatus.enabled.value,
        ).values_list('entity_id', flat=True)
        return list(rg_enabled_ids)

    def add_child_ids(self, rg_ids):
        from modjento.models import CatalogProductSuperLink
        mp_kids = CatalogProductSuperLink.objects.get_child_map()
        ms_ids = set(rg_ids)
        rg_new = copy.copy(rg_ids)
        for x in rg_ids:
            rg_child_ids = mp_kids.get(x)
            if not rg_child_ids:
                continue
            for y in rg_child_ids:
                if y not in ms_ids:
                    rg_new.append(y)
        return rg_new

    def get_visible_and_children(self):
        rg_ids = self.get_visible_ids()
        return self.add_child_ids(rg_ids)


def _initialize_managers():
    from modjento.models import (CatalogProductEntity, EavAttribute,
                                 EavAttributeOption, EavAttributeOptionValue)
    EavAttributeOptionValue.add_to_class('objects', EavOptionValueManager())
    EavAttributeOption.add_to_class('objects', EavOptionManager())
    EavAttribute.add_to_class('objects', EavAttributeManager())
    CatalogProductEntity.add_to_class('objects', ProductManager())

_initialize_managers()
