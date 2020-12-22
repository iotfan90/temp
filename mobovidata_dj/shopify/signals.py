from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import MasterCategory, Model


@receiver(m2m_changed, sender=Model.categories.through)
def my_handler(sender, **kwargs):
    model = kwargs['instance']
    action = kwargs['action']
    if kwargs['pk_set']:
        categories = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])
        if action == 'post_add':
            hyp_brand = '-'.join(model.brand.name.lower().split())
            hyp_model = '-'.join(model.model.lower().split())

            for category in categories:
                mcid = MasterCategory.get_next_available_mcid()
                obj, created = MasterCategory.objects.get_or_create(
                    category_url=category.attribute_set_url,
                    hyphenated_brand_model_name='{}-{}'.format(hyp_brand,
                                                               hyp_model),
                    defaults={'brand_model_name': '{} {}'.format(model.brand.name,
                                                                 model.model),
                              'brand_model_url': '{} {}'.format(hyp_brand,
                                                                hyp_model),
                              'brand_name': model.brand.name, 'brand_url': hyp_brand,
                              'category_name': category.attribute_set_name,
                              'mcid': mcid, 'model_name': model,
                              'model_url': hyp_model},
                )
        else:
            pass
