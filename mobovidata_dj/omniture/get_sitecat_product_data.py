import datetime

from mobovidata_dj.omniture.omniture_py import OmniturePy


class SiteCatProductReport(object):
    username = None
    secret = None
    report_suite_id = None
    first_product_id = 0
    PAGE_VIEWS_IDX = 0
    VISITS_IDX = 1
    ORDERS_IDX = 2
    DEFAULT_REPORT_SIZE = 50
    omniture = None
    normalized_report_data = {}

    def __init__(self, username, secret, report_suite_ids, product_ids=None):
        self.username = username
        self.secret = secret
        self.report_suite_ids = report_suite_ids
        self.product_ids = product_ids
        self.omniture = OmniturePy(self.username, self.secret)
        self.top = len(product_ids)

    """
        The SiteCat API breaks up the report data into chunks based on the
        dateGranularity.
        Even if we use year for the granularity we will run into time when the
        date range crosses those boundaries.  This method merges(adds) the
        counts and page views together and puts them into a more mangeable data
        structure.
    """
    def normalize_and_merge_data(self, data):
        for d in data:
            for prod in d['breakdown']:
                res_prod = self.normalized_report_data.get(prod['name'], None)
                if res_prod is None:
                    self.normalized_report_data[prod['name']] = {
                        'page_views': int(prod['counts'][self.PAGE_VIEWS_IDX]),
                        'visits': int(prod['counts'][self.VISITS_IDX]),
                        'orders': int(prod['counts'][self.ORDERS_IDX])
                    }
                else:
                    self.normalized_report_data[prod['name']]['page_views'] += int(prod['counts'][self.PAGE_VIEWS_IDX])
                    self.normalized_report_data[prod['name']]['visits'] += int(prod['counts'][self.VISITS_IDX])
                    self.normalized_report_data[prod['name']]['orders'] += int(prod['counts'][self.ORDERS_IDX])

        return self.normalized_report_data

    def get_report_request_obj(
            self,
            report_suite_id,
            date_from,
            date_to,
            page=0,
            size=None):
        if size is None:
            size = self.DEFAULT_REPORT_SIZE
        report_obj = {
            'reportDescription': {
                'reportSuiteID': report_suite_id,
                'dateFrom': (datetime.datetime.strftime(date_from, '%Y-%m-%d')),
                'dateTo': datetime.datetime.strftime(date_to, '%Y-%m-%d'),
                'dateGranularity': 'day',
                'metrics': [
                    {'id': 'pageviews'},
                    {'id': 'visits'},
                    {'id': 'orders'},
                    {'id': 'cart additions'},
                    {'id': 'cart removals'},
                ],
                'elements': [
                    {
                        'id': 'product',
                        'classification': 'Item ID',
                        'startingWith':  (page * size) + 1,
                        'top': self.top,
                        'search': {
                            'type': 'or',
                            'keywords': self.product_ids
                        },
                    },
                ]
            }
        }

        return report_obj

    def get_report(self, report_suite_id, date_from, date_to, page=0, size=10):
        report_obj = self.get_report_request_obj(report_suite_id, date_from,
                                                 date_to, page, size)

        data = self.omniture.run_omtr_queue_and_wait_request('Report.QueueTrended', report_obj)
        norm_data = self.normalize_and_merge_data(data['report']['data'])
        return data, norm_data

    def get_report_data(self, report_suite_id, date_from, date_to, page=0,
                        size=10):
        print 'Report Suite: %s Getting Page: %s' % (report_suite_id, page)
        report_data = self.get_report(report_suite_id, date_from=date_from,
                                      date_to=date_to, page=page, size=size)
        print 'Report Size: %s' % len(report_data)
        """
            Since we have to page through the report results, this makes sure
            we're really at the last page we set first_product_id to the first
            item in the page.  If we have a situation where the last page is
            exactly the size of our page size, this first_product_id check
            should fail and stop the recursion.
        """
        product_ids = report_data[1].keys()

        if len(report_data) == size and self.first_product_id != product_ids[0]:
            self.first_product_id = product_ids[0]
            next_page = page + 1
            self.get_report_data(
                report_suite_id,
                date_from=date_from,
                date_to=date_to,
                page=next_page,
                size=size
            )

    # def get_reports(self, date_from, date_to, page=0, size=10):
    #     for report_suite_id in self.report_suite_ids:
    #         self.get_report_data(report_suite_id=report_suite_id,date_from=date_from,date_to=date_to,size=self.DEFAULT_REPORT_SIZE)
    #     print 'Updating the sitecat_product_data table'
    #     current_ids = set(SiteCatProductData.objects.values_list('product_id', flat=True))
    #     product_ids = set(self.normalized_report_data.keys())
    #     to_update = product_ids & current_ids
    #     to_create = product_ids - current_ids
    #     to_delete = current_ids - product_ids
    #     new_items = []
    #     for product_id, counts in self.normalized_report_data.items():
    #         if product_id in to_update:
    #             SiteCatProductData.objects.filter(product_id=product_id).update(
    #                 page_views=counts['page_views'],
    #                 visits=counts['visits'],
    #                 orders= counts['orders'])
    #         elif product_id in to_create:
    #             new_items = [ SiteCatProductData(
    #                 product_id=product_id,
    #                 page_views=counts['page_views'],
    #                 visits=counts['visits'],
    #                 orders=counts['orders']
    #             ) ]
    #     SiteCatProductData.objects.bulk_create(new_items)
    #     SiteCatProductData.objects.filter(product_id__in=to_delete).delete()
