import boto3
import csv
import json
import os
import pandas as pd
import paramiko
import urllib2
import time
import traceback
import zipfile

from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from pg8000.core import InterfaceError

from .utils import map_facebook_feed
from mobovidata_dj.bigdata.utils import get_redshift_connection
from modjento.models import (CatalogProductEntity, CatalogProductEntityDatetime,
                             CatalogProductEntityInt)


logger = get_task_logger(__name__)


@shared_task(ignore_results=True)
def make_feeds(feed_dir=settings.PRODUCT_FEED_DIR):
    """
    Manages feed downloads and transformations
    @param str feed_dir: Path to directory where the feed will be downloaded
    @return void
    """
    cache_key = 'feed_run'
    last_run = cache.get(cache_key)
    now = datetime.now()
    status = cache.get('feed_run_status')
    if last_run:
        time_since_last_run = now - last_run
        hours_since = time_since_last_run.total_seconds() / 60 / 60
        # If the process was run within 5 minutes, we should return so the
        # caller can move on to the next campaign
        if hours_since < 23:
            return 'continue on...'
        if status == 'active':
            # if status is pending we don't want to queue the task
            return 'continue on...'
    cache.set('feed_run_status', 'active', 60)
    if not os.path.exists(feed_dir):
        os.makedirs(feed_dir)
    feed_path = None
    max_retries = 3
    for _ in xrange(max_retries):
        try:
            feed_path = download_feed(feed_dir)
            break
        except Exception as ex:
            logger.exception('The is an error while downloading the file %s',
                             ex)
        time.sleep(10)
    if feed_path:
        make_zaius_feed(feed_path)
        # make_facebook_feed(feed_path)
        # responsys_feed = make_responsys_feed(feed_path)
        # post_responsys_feed(responsys_feed)
        # make_separate_fb_feeds(feed_path)
        # make_facebook_bluetooth_feed(feed_path)
        os.remove(feed_path)
    cache.set('feed_run_status', 'complete', 60)
    cache.set(cache_key, now, None)


def get_product_group_by_sku(sku):
    """
    Get product group label using SKU product identifier.
    :param str sku: product identifier (it's not the product id)
    :return: str Product group label
    """
    product_group = 'none'
   # if sku is None:
        sku = '1'

    #if '-BF' in sku:
        product_group = 'Butterfly 1.0'
    #elif '-2BF' in sku:
        product_group = 'Butterfly 2.0'
    #elif '-DTW' in sku:
        product_group = 'Compact'
    #elif '-CLW' in sku:
        product_group = 'Compact Clutch'
    #elif '-DRF' in sku:
        product_group = 'Dragonfly'
    #elif '-2DRC' in sku:
        product_group = 'Dream Catcher'
    #elif '-HB' in sku:
        product_group = 'Hummingbird'
    #elif '-MGS' in sku:
        product_group = 'Luxury'
    #elif '-WC' in sku:
        product_group = 'Multi Card'
    #elif '-DRV' in sku:
        product_group = 'Printed'
    #elif '-CSO' in sku:
        product_group = 'Slideout'
    #return product_group


def get_products_enabled(last_days):
    """
    Get a set of products that were enabled in the @last_days.
    :param int last_days: how many days back the query should be
    :return: set of SKU (product attr.)
    """
    dt_last_days = timezone.now() - timedelta(days=last_days)

    entity_int_ids = (CatalogProductEntityInt.objects.using('magento')
                      .filter(entity_type_id=4,
                              attribute__attribute_id=96, value=1)
                      .values_list('entity', flat=True))

    entity_datetime_ids = (CatalogProductEntityDatetime.objects
                           .using('magento')
                           .filter(attribute__attribute_id=424,
                                   value__gt=dt_last_days)
                           .values_list('entity', flat=True))

    # Intersection between entity_int_ids and entity_datetime_ids
    entity_ids = list(set.intersection(set(entity_int_ids),
                                       set(entity_datetime_ids)))

    entities_sku = (CatalogProductEntity.objects.using('magento')
                    .filter(entity_id__in=entity_ids).order_by('sku')
                    .values_list('sku', flat=True))
    # It's more efficient to look up in a set than in a list
    entities_sku_set = set(entities_sku)
    return entities_sku_set


def get_products_back_in_stock(last_days):
    """
        Get a set of products that had come back in stock in the @last_days.
        :param int last_days: how many days back the query should be
        :return: set of products ids
    """
    products_id_set = set()
    try:
        cnx = get_redshift_connection()
        cur = cnx.cursor()
        query = """
            SELECT DISTINCT t.product_id
            FROM reports.inventory_qty_new t
            WHERE t.product_id IN
                (
                SELECT t1.product_id
                FROM reports.inventory_qty_new t1
                WHERE t1.qty <= 0
                    AND t1.created_at > dateadd(day,-%s,'now')
                    AND t1.product_id IN
                        (
                        SELECT t2.product_id
                        FROM reports.inventory_qty_new t2
                        WHERE t2.product_id = t1.product_id
                            AND t2.qty > 10
                            AND t2.created_at > t1.created_at
                            AND NOT EXISTS
                                (
                                SELECT t3.product_id
                                FROM reports.inventory_qty_new t3
                                WHERE t3.product_id = t2.product_id
                                    AND t3.qty <= 10
                                    AND t3.created_at > t2.created_at
                                )
                        )

                )
        """ % last_days
        cur.execute(query)
        results = cur.fetchall()
    except InterfaceError as e:
        tb = traceback.format_exc()
        error_msg = 'Redshift Database connection failed | %s | %s' % (e, tb)
        logger.exception('Redshift Database connection failed', extra=locals())
    else:
        # It's more efficient to look up in a set than in a list
        products_id_set = set([x[0] for x in results])

    return products_id_set


def make_zaius_feed(feed_path):
    z_headers = {
        'color': 'color',  # custom field
        'price': 'retail_price',  # custom field
        'large_image': 'image_url',
        'title': 'name',
        'pid': 'product_id',
        'model': 'phone_model',  # custom field
        'brand': 'brand',
        'sale_price': 'price',
        'url': 'link',  # custom field
        #  'adwords_labels': 'product_category',
        'skuid': 'sku',
        'crumbs': 'crumbs',
        'parent_product_id': 'parent_product_id',
        'cat_id': 'cat_id',
        'product_group': 'product_group',
        'new_product_l7d': 'new_product_l7d',
        'back_in_stock': 'back_in_stock',
        #  'product_type': 'category'
    }

    feed = pd.read_csv(feed_path, sep='\t')
    feed['large_image'] = 'https:' + feed['large_image']
    feed['crumbs'] = feed['crumbs'].str.replace('HOME\|', '')
    feed['category'] = feed['crumbs'].str.replace('\|', ' > ')
    split_ids = feed['pid'].str.split('_')
    feed['parent_product_id'] = split_ids.apply(lambda x: x[0])
    feed['cat_id'] = split_ids.apply(lambda x: x[-1])
    feed['product_group'] = feed['skuid'].apply(
        lambda x: get_product_group_by_sku(x))
    products_enabled = get_products_enabled(7)
    feed['new_product_l7d'] = (feed['skuid']
                               .apply(lambda x: 1 if x in products_enabled else 0))
    products_back_in_stock = get_products_back_in_stock(7)
    feed['back_in_stock'] = split_ids.apply(
        lambda x: 1 if int(x[0]) in products_back_in_stock else 0)
    feed = feed[[k for k in z_headers.keys()]]
    feed = feed.rename(columns=z_headers)
    # feed['link'] = feed.link.apply(lambda x:x[0:x.index('?')])
    feed.to_csv('%szaius_products_%s.csv' % (settings.PRODUCT_FEED_DIR, datetime.today().strftime('%Y-%m-%d')),
                index=False)
    s3 = boto3.resource('s3')
    data = open('%szaius_products_%s.csv' % (settings.PRODUCT_FEED_DIR, datetime.today().strftime('%Y-%m-%d')), 'rb')
    b = s3.Bucket('zaius-incoming')
    b.put_object(Key='5YVK2LhYpKWTjZ4G035Dlw/zaius_products_%s.csv' % datetime.today().strftime('%Y-%m-%d'), Body=data)
    os.remove('%szaius_products_%s.csv' % (settings.PRODUCT_FEED_DIR, datetime.today().strftime('%Y-%m-%d')))


def post_responsys_feed(responsys_feed):
    """
    Posts the responsys_feed to the Responsys FTP
    @param str responsys_feed:
    @return void
    """
    private_key = paramiko.RSAKey.from_private_key_file(settings.RESPONSYS_FTP['pkey'])
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(settings.RESPONSYS_FTP['url'],
                username=settings.RESPONSYS_FTP['user'], password='',
                pkey=private_key)
    ftp = ssh.open_sftp()
    ftp.put(
        responsys_feed, os.path.join(
            settings.RESPONSYS_FEED['destination'],
            responsys_feed.split('/')[-1]
        ), callback=None
    )
    try:
        os.remove(responsys_feed)
    except:
        logger.error('Could not remove responsys feed', extra=locals())


def make_responsys_feed(feed_path):
    """
    @param str feed_path: Path to downloaded feed.
    @return str: Path to the local responsys feed
    """
    product_sales = {
        r['product_id']: {
            '90_day': r['day_90'], '7_day': r['day_7'], '14_day': r['day_14']
        } for r in json.loads(cache.get('salesreport:products'))
    }
    responsys_rows = []
    responsys_cols = settings.RESPONSYS_COLUMN_MAP
    with open(feed_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for i, row in enumerate(reader):
            if 'MOB-UNI-WSLV' in row.get('mpn'):
                continue
            responsys_row = {v: row[k] for k, v in responsys_cols.iteritems()}
            product_id = int(row['id'].split('_')[0])
            run_rates = product_sales.get(product_id, {})
            responsys_row.update({
                'RUNRATE_90D': run_rates.get('90_day', 0),
                'RUNRATE_7D': run_rates.get('7_day', 0),
                'RUNRATE_14D': run_rates.get('14_day', 0),
                'PRODUCT_LINK': '%s%s' % (row['link'].split('?')[0],
                                          settings.RESPONSYS_FEED['tracking_string'])
            })
            responsys_rows.append(responsys_row)
    with open(settings.RESPONSYS_FEED['feed_name'], 'w') as o:
        writer = csv.DictWriter(o, fieldnames=responsys_rows[0].keys())
        writer.writeheader()
        writer.writerows(responsys_rows)
    return os.path.join(settings.PRODUCT_FEED_DIR, 'resp_co_com.csv')


def make_facebook_feed(feed_path):
    """
    @param str feed_path: Path to downloaded feed
    @return str: Path to the local facebook feed
    """
    fb_rows = errors = []
    with open(feed_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for i, row in enumerate(reader):
            map_facebook_feed(row, fb_rows, i, errors)
    with open(settings.FACEBOOK_FEED['feed_name'], 'wb') as o:
        writer = csv.DictWriter(o, fieldnames=fb_rows[0].keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(fb_rows)
        fb_rows[:] = []
    return settings.FACEBOOK_FEED['feed_name']


def make_separate_fb_feeds(feed_path):
    """
    @param str feed_path: Path to downloaded feed
    @return str: Path to the local facebook feed
    """
    fb_rows = errors = []
    product_ids = settings.FACEBOOK_SEPERATE_IDS
    with open(feed_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for i, row in enumerate(reader):
            if not row.get('id'):
                continue
            p_id = row['id'].split('_')[0] if len(row['id'].split('_')) > 0 else row['id']
            if p_id not in product_ids:
                continue
            map_facebook_feed(row, fb_rows, i, errors)
    with open(settings.FACEBOOK_FEED['separate_feed_name'], 'wb') as o:
        writer = csv.DictWriter(o, fieldnames=fb_rows[0].keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(fb_rows)
        fb_rows[:] = []
    return settings.FACEBOOK_FEED['separate_feed_name']


def make_facebook_bluetooth_feed(feed_path):
    """
    Create Facebook feed that contains only Universal Bluetooth products
    @param str feed_path: Path to downloaded feed
    @return str: Path to local Facebook Bluetooth feed
    """
    bt_rows = errors = []
    with open(feed_path, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for i, row in enumerate(reader):
            # Filter for Universal Bluetooth products
            if 'Bluetooth' in row.get('Custom Label 1') and row.get('c:cell_phone_model') == 'Universal':
                map_facebook_feed(row, bt_rows, i, errors)
    with open(settings.FACEBOOK_FEED['facebook_bluetooth_feed'], 'wb') as bt_feed:
        writer = csv.DictWriter(bt_feed, fieldnames=bt_rows[0].keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(bt_rows)
    return settings.FACEBOOK_FEED['facebook_bluetooth_feed']


def download_feed(st_directory):
    if not os.path.exists(st_directory):
        os.makedirs(st_directory)
    feed_path = os.path.join(st_directory, settings.BLOOMREACH_FEED_CO.split('/')[-1])
    # result = urllib.urlretrieve(settings.GOOGLEBASE_FEED_CO, feed_path)
    zip_file = urllib2.urlopen(settings.BLOOMREACH_FEED_CO)
    with open(feed_path, 'wb') as output:
        output.write(zip_file.read())
    with zipfile.ZipFile(feed_path, 'r') as f_zip:
        f_zip.extractall(st_directory)
    os.remove(feed_path)
    return feed_path.replace('.zip', '.txt')
