from django.conf import settings

from .models import SiteCatProductData
from get_sitecat_product_data import SiteCatProductReport
from modjento.models import CatalogProductEntity

"""
Workflow:
    Currently, the recommended method for running these methods is through a local shellplus notebook
    or through shellplus on the production server.
    1. Run `get_pdp_view_report` passing it product ID's and timespan (days),
       this returns a tuple(data, normalized data)

    2. Pass the first element from tuple and your list of product ids into `get_pdp_view_data`,
       this returns a list of dictionaries with counts for each product ID

    3. Pass the return value from step 2 and the list of product ids into `update_sc_product_data_table`,
       this will update the table
"""


def get_pdp_view_report(rg_product_ids, start_date, end_date):
    """
    Compiles report from SiteCat for given product ID's over specified timespan
    :param rg_product_ids: list[int] representing visible product ID's
    :param start_date: datetime object for the start of the daterange
    :param end_date: datetime object for the end of the daterange
    :return: dict containing date, product id, page views, & visits
    """
    username = settings.OMNITURE_CREDENTIALS['username']
    secret = settings.OMNITURE_CREDENTIALS['secret']
    report_suite_ids = settings.OMNITURE_CREDENTIALS['report_suite_ids']
    rg_product_ids = ['^%s$' % i for i in rg_product_ids]
    # Instantiate SiteCat object
    sc = SiteCatProductReport(
        username=username,
        secret=secret,
        report_suite_ids=report_suite_ids,
        product_ids=rg_product_ids
    )
    # Fetch report from SiteCat
    data, norm_data = sc.get_report(report_suite_ids[0], start_date, end_date)
    return data, norm_data


def quickreport(norm_data, rg_product_ids, report_data):
    """
    Combines counts reported for duplicate product ID's and returns dictionary with total
    page views, visits, and orders over entire time period
    :param norm_data: dict of normalized data report from SiteCat
    :param rg_product_ids: list[int] of product ids under question
    :param report_data: dict of raw data report from SiteCat
    :return: dict
    """
    merged_product_data = {
        '%s' % pid: {'page_views': 0, 'visits': 0, 'orders': 0} for pid in rg_product_ids
    }
    # Populate dict with orders, page views, and visits
    for pid in rg_product_ids:
        a = [norm_data[key] for key in norm_data if key.split('_')[0] == '%s' % pid]
        for each in a:
            merged_product_data[str(pid)]['orders'] += each.get('orders')
            merged_product_data[str(pid)]['page_views'] += each.get('page_views')
            merged_product_data[str(pid)]['visits'] += each.get('visits')
    # Update dict with time period
    merged_product_data.update({'period': report_data['report']['period']})
    return merged_product_data


def get_pdp_view_data(sc_report_data, rg_product_ids):
    """
    Process report from SiteCatalyst and consolidate data into list of dictionaries
    containing date, product ID's, and counts of page views, visits, & orders
    :param sc_report_data: dictionary of report from SiteCatalyst
    :param rg_product_ids: list of visible product id's
    :return: list[dict]
    """
    rows = []
    for brk in sc_report_data['report']['data']:
        row = {'day': '%s-%s-%s' % (brk['year'], brk['month'], brk['day']) }
        for pid in rg_product_ids:
            counts = [
                map(int, data['counts']) for data in brk['breakdown'] if data.get('name', '').split('_')[0] == '%s' % pid
            ]
            page_views = visits = orders = cart_adds = cart_removes = 0
            for x in counts:
                page_views += x[0]
                visits += x[1]
                orders += x[2]
                cart_adds += x[3]
                cart_removes += x[4]
            merged_counts = [page_views, visits, orders, cart_adds, cart_removes]
            row.update({
                '%s' % pid: merged_counts
            })
        rows.append(row)
    return rows


def update_sc_product_data_table(data_rows, rg_product_ids):
    """
    Formats date into correct format YYYY-MM-DD and updates SiteCatProductData table
    for each date and product ID
    :param data_rows: list[dict] returned from get_pdp_view_data function
    :param rg_product_ids: list of visible product ID's
    """
    skus = CatalogProductEntity.objects.filter(entity_id__in=rg_product_ids).values('entity_id', 'sku')
    skus = {'%s' % r['entity_id']: r['sku'] for r in skus}
    data_to_load = []
    prim_keys = []
    for r in data_rows:
        int_date = r['day'].replace('-', '')
        for k in r:
            if k != 'day':
                prim_keys.append(int('%s%s' % (k, int_date)))
    existing = SiteCatProductData.objects.filter(product_id_date__in=prim_keys).values('product_id_date')
    existing = [r['product_id_date'] for r in existing]
    existing_keys = []
    for r in data_rows:
        current_date = r['day']
        int_date = current_date.replace('-', '')
        data_to_load = []
        existing_keys = []
        existing = SiteCatProductData.objects.get()
        existing = [r.id for r in existing]
        for k, v in r.items():
            if k == 'day':
                continue
            pk = int('%s%s' % (k, int_date))
            if pk in existing:
                existing_keys.append(pk)
                continue
            data_to_load.append(SiteCatProductData(
                    product_id_date= pk,
                    date= current_date,
                    product_id= k,
                    page_views= v[0],
                    visits= v[1],
                    sku=skus.get(k),
                    cart_adds=v[3],
                    cart_removes=v[4],
                ))
    SiteCatProductData.objects.bulk_create(data_to_load)
