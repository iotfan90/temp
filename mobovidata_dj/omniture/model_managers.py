import logging

from django.db.models import Manager
from djenga.profiling import end_timer, start_timer

logger = logging.getLogger(__name__)


class SiteCatDataManager(Manager):
    def all_data(self):
        mp_data = getattr(self, 'mp_data', None)
        if mp_data is not None:
            return mp_data
        start_timer(logger, 'Loading all sitecat data', True)
        qs_all = self.all()
        mp_data = {
            x.product_id: x
            for x in qs_all
        }
        setattr(self, 'mp_data', mp_data)
        end_timer()
        return mp_data
