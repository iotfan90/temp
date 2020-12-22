from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Historically updates all CustomerOrder objects with first_visit data'

    def handle(self, *args, **options):
        from mobovidata_dj.analytics.models import CustomerOrder
        for order in CustomerOrder.objects.all():
            copy_first_denormalized = ['url_path', 'product_fullid',
                            'url_parameters', 'created_dt']
            first_visit = order.session.first_visit()

            if not first_visit: continue

            for field in copy_first_denormalized:
                new_val = getattr(first_visit, field, None)
                if new_val:
                    setattr(order, 'first_visit_%s'%field, new_val)

            order.save()
