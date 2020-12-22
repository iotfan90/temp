import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class MagentoRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'modjento':
            return 'magento'
        if model._meta.app_label == 'mobovidata_legacy':
            return 'mobovidata_legacy'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'modjento':
            if 'magento_write' in settings.DATABASES:
                return 'magento_write'
            return 'magento'
        return 'default'


    # Note: the default implementation will check if the two objects are
    # located in the same database, and this is what we want.
    # def allow_relation(self, obj1, obj2, **hints):
    #     if obj1._meta.app_label != obj2._meta.app_label:
    #         return False
    #     return True

    def allow_relation(self, obj1, obj2, **hints):
        if (
                (
                    obj1._meta.app_label == 'modjento' and obj2._meta.app_label != 'modjento'
                ) or (
                    obj1._meta.app_label == 'mobovidata_legacy' and obj2._meta.app_label != 'mobovidata_legacy'
                )
        ) or (
            (
                obj2._meta.app_label != 'modjento' and obj2._meta.app_label == 'modjento'
            ) or (
                obj2._meta.app_label != 'mobovidata_legacy' and obj2._meta.app_label == 'mobovidata_legacy'
            )
        ):
            return False
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'magento' or app_label == 'modjento' or db == 'mobovidata_legacy' or app_label == 'mobovidata_legacy':
            return False
        return True


class MobovidataLegacyRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'mobovidata_legacy':
            return 'mobovidata_legacy'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'mobovidata_legacy':
            if 'mobovidata_legacy_write' in settings.DATABASES:
                return 'mobovidata_legacy_write'
            return 'mobovidata_legacy'
        return 'default'

    # Note: the default implementation will check if the two objects are located in the same
    # database, and this is what we want.
    # def allow_relation(self, obj1, obj2, **hints):
    #     if obj1._meta.app_label != obj2._meta.app_label:
    #         return False
    #     return True

    def allow_relation(self, obj1, obj2, **hints):
        if (
           obj1._meta.app_label == 'mobovidata_legacy' and obj2._meta.app_label != 'mobovidata_legacy'
        ) or (
            obj2._meta.app_label != 'mobovidata_legacy' and obj2._meta.app_label == 'mobovidata_legacy'
        ):
            return False
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'mobovidata_legacy' or app_label == 'mobovidata_legacy':
            return False
        return True


class MobovidataLegacyRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'mobovidata_legacy':
            return 'mobovidata_legacy'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'mobovidata_legacy':
            if 'mobovidata_legacy_write' in settings.DATABASES:
                return 'mobovidata_legacy_write'
            return 'mobovidata_legacy'
        return 'default'

    # Note: the default implementation will check if the two objects are located in the same
    # database, and this is what we want.
    # def allow_relation(self, obj1, obj2, **hints):
    #     if obj1._meta.app_label != obj2._meta.app_label:
    #         return False
    #     return True

    def allow_relation(self, obj1, obj2, **hints):
        if (
           obj1._meta.app_label == 'mobovidata_legacy' and obj2._meta.app_label != 'mobovidata_legacy'
        ) or (
            obj2._meta.app_label != 'mobovidata_legacy' and obj2._meta.app_label == 'mobovidata_legacy'
        ):
            return False
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'mobovidata_legacy' or app_label == 'mobovidata_legacy':
            return False
        return True
