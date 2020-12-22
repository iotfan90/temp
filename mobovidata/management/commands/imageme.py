# encoding: utf-8
from __future__ import unicode_literals

import codecs
import csv
import os
import urllib

from collections import OrderedDict
from datetime import date
from django.core.management.base import BaseCommand
from djenga.csv import UnicodeCsvWriter
from djenga.mixins import LoggingMixin

from mobovidata_dj.facebook.connect import FacebookConnect
from modjento.models import CatalogProductEntity, EavAttribute


class Command(LoggingMixin, BaseCommand):
    help = (
        'The mobovida_fb command generates a CSV file of product info'
    )
    # args = '<~/mobovida.csv>'

    def add_arguments(self, parser):
        """
        :type parser: argparse.ArgumentParser
        """
        parser.add_argument(
            '-i', '--file',
            default='products.csv',
            dest='st_csv_file',
            help='This csv file contains the product ids'
        )

    def __init__(self, connection_settings=None, infile=None, outfile=None,
                 is_main=False):
        super(Command, self).__init__()

        self.infile = None
        """@type: str | unicode"""
        self.outfile = None
        """@type: str | unicode"""
        self.products = OrderedDict()
        """@type: OrderedDict"""
        self.connection = None
        """@type: MySQLdb.Connection"""
        self.st_directory = ''
        self.product_ids = []
        self.st_zip_filename = ''
        self.local_image_paths = OrderedDict()

        self.is_main = is_main
        if not is_main:
            self.infile = infile
            """@type: str | unicode"""
            if not outfile:
                self.generate_filename()
            else:
                self.outfile = outfile
            """@type: str | unicode"""

    def generate_filename(self):
        st_directory = os.path.expanduser('~/Desktop')
        if not os.path.isdir(st_directory):
            st_directory = os.path.expanduser('~')
        dt_today = date.today()
        st_filename = dt_today.strftime('facebook.%Y%m%d.csv')
        st_path = os.path.join(st_directory, st_filename)
        n = 0
        while os.path.exists(st_path):
            n += 1
            st_filename = dt_today.strftime('facebook.%%Y%%m%%d.%02d.csv' % n)
            st_path = os.path.join(st_directory, st_filename)
        self.outfile = st_path

    def load_input(self):
        with open(self.infile, 'rU') as f:
            f_in = csv.reader(f)
            rg_header = f_in.next()
            for x in f_in:
                mp_values = dict(zip(rg_header, x))
                self.products[int(mp_values['product_id'])] = mp_values

    def get_product_link(self, url):
        if not url:
            return ''
        st_format = '%s%s' if url[-1] == '/' else '%s%s/'
        st_url = st_format % ('http://www.cellularoutfitter.com/', url)
        st_url = st_url.replace('http', 'https')
        return st_url

    def get_image_url(self, image):
        if not image:
            return image
        if image.startswith('URL/'):
            image = image.replace('URL',
                                  'http://cellularoutfitter.com/media/catalog/'
                                  'product')
        else:
            image = ('http://cellularoutfitter.com/media/catalog/product/%s' %
                     (image,))
        return image

    def load_product(self):
        rg_fields = (list(CatalogProductEntity._meta.get_all_field_names()) +
                     list(EavAttribute.objects.filter(entity_type_id=4)
                          .values_list('attribute_code', flat=True)))

        self.product_ids = [k for k in self.products.keys()]

        attributes = EavAttribute.objects.get_values(
                self.product_ids,
                entity_type=4,
                field_names=rg_fields)
        qs_products = CatalogProductEntity.objects.filter(
            entity_id__in=self.product_ids)
        rg_products = [x.to_json() for x in qs_products]
        for x in rg_products:
                n_id = x['entity_id']
                x.update(attributes.get(n_id, {}))
        self.products = OrderedDict()
        for r in rg_products:
            self.products[int(r['entity_id'])] = r
        return rg_products

    def make_dirs(self):
        self.st_directory = './data/facebook_images'
        if not os.path.exists(self.st_directory):
            os.makedirs(self.st_directory)

    def download_images(self):
        self.make_dirs()
        for x in self.products.itervalues():
            product_types = [t.strip() for t in x['product_type'].split('&')]
            types = '&'.join(x for x in product_types)
            product_type = types.lower().replace(' ', '-')
            product_id = x['entity_id']
            img_keys = ['image']
            for key in img_keys:
                st_image = x.get(key)
                st_image_url = self.get_image_url(st_image)
                img_name = st_image.split('/')[-1]
                image_path = os.path.join(self.st_directory, img_name)
                urllib.urlretrieve(st_image_url, image_path)
                old_path = os.path.join(self.st_directory, img_name)
                new_path = os.path.join(self.st_directory, '%s_%s.jpg' %
                                        (product_type, product_id))
                print(old_path, new_path)
                os.rename(old_path, new_path)
                x['local_' + key] = new_path

    def create_mobovida_csv(self):
        fieldnames = []
        for x in self.products.itervalues():
            fieldnames = [k for k in x]
            break
        with open(self.outfile, 'wb') as f:
            print('Creating output file [%s]' % (self.outfile,))
            cus_csv = codecs.open(self.outfile, 'wb', encoding='utf-8')
            cus_writer = UnicodeCsvWriter(cus_csv)
            cus_writer.writerow([unicode(x) for x in fieldnames])
            for x in self.products.itervalues():
                product_row = [x.get(field, '') for field in fieldnames]
                cus_writer.writerow(product_row)

    def add_image_hashes(self, image_hashes, products=None):
        """
        Accepts an ordered dict containing tuples of local_path,
        fb_hash for each image of each product
        """
        if not products:
            products = self.products
        for x in image_hashes:
            product_hashes = image_hashes[x]
            product = products[x]
            hash_keys = [k for k in product_hashes if '_hash' in k]
            for k in hash_keys:
                product[k] = product_hashes[k]
                print(product[k])

    def create_csv(self):
        FIELDS = [
            'Link',
            'Name',
            'Description',
            'Image',
            'Image Crops',
            'Video ID',
            'Mobile Deep Link',
        ]
        print('Creating output file [%s]' % (self.outfile,))
        with open(self.outfile, 'wb') as f:
            f_out = csv.writer(f)
            for n in xrange(0, 3):
                row = []
                for n_product, x in enumerate(self.products.itervalues()):
                    for y in FIELDS:
                        if n > 0:
                            row.append(x.get(y, ''))
                        else:
                            row.append('Product %d - %s' % (n_product + 1, y))
                f_out.writerow(row)
                FIELDS[1] = 'Name #%d' % (n + 1)
            FIELDS[3] = 'Image 1200'
            for n in (1, 2,):
                row = []
                for n_product, x in enumerate(self.products.itervalues()):
                    for y in FIELDS:
                        if n > 0:
                            row.append(x.get(y, ''))
                        else:
                            row.append('Product %d - %s' % (n_product + 1, y))
                f_out.writerow(row)
                FIELDS[1] = 'Name #%d' % (n + 1)
            f_out.writerow([])
            FIELDS = [
                'product_id',
                'Link',
                'Name #1',
                'Name #2',
                'Description',
                'Image',
                'Image 1200',
                'image_hash'
            ]
            f_out.writerow(FIELDS)
            for x in self.products.itervalues():
                row = [ x.get(y, '') for y in FIELDS ]
                f_out.writerow(row)

    def upload_images(self):
        fb = FacebookConnect()
        for x in self.products.itervalues():
            local_image = x.get('local_image')
            self.info('uploading %s to facebook', local_image)
            if local_image:
                img_hash = fb.upload_image(local_image)
                x['image_hash'] = img_hash

    def create_carousel_ad(self):
        fb = FacebookConnect()
        from facebookads.specs import LinkData, AttachmentData
        link = LinkData()
        link[link.Field.link] = 'http://www.cellularoutfitter.com'
        link[link.Field.message] = '<please enter message text>'
        link[link.Field.child_attachments] = list()
        rg_products = self.products
        for single_product in rg_products.itervalues():
            product = AttachmentData()
            product[AttachmentData.Field.link] = self.get_product_link(
                single_product['url_path'])
            product[AttachmentData.Field.name] = single_product['name']
            d_special_price = single_product.get('special_price', '')
            if d_special_price:
                st_description = ('On sale for $%.2f ; usually %.2f' %
                                  (d_special_price, single_product['price'],))
            else:
                st_description = ('Every day low price of $%.2f (MSRP: %.2f)' %
                                  (single_product['price'],
                                   single_product['msrp'],))
            product[AttachmentData.Field.description] = st_description
            product[AttachmentData.Field.image_hash] = \
                single_product['image_hash']
            link[link.Field.child_attachments].append(product)
        link[link.Field.caption] = 'cellularoutfitter.com'
        fb.create_carousel_ad(link)

    def handle(self, st_csv_file, *args, **options):
        self.infile = st_csv_file
        self.load_input()
        self.load_product()
        self.download_images()
        self.upload_images()
        self.create_carousel_ad()
        return 'Images uploading done'
