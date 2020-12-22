from __future__ import unicode_literals
from datetime import datetime
from collections import  defaultdict
import os
import pytz
import re
import urllib
from urlparse import urljoin
import logging
from django.conf import settings
from modjento.models import EavAttribute, ReviewEntitySummary
from modjento.models import CatalogProductEntity, CataloginventoryStockItem
from modjento.models import CatalogProductEntityMediaGalleryValue as MediaGalleryValue
from mobovidata_dj.shopify.models import ProductVariant, ProductImage
from .connect import FacebookConnect
from facebookads.specs import LinkData, AttachmentData
from facebookads.exceptions import FacebookRequestError
import requests
import shutil
import json

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

logger = logging.getLogger(__name__)


def get_stars(product):
    star_number = int(round(product['rating_summary']))
    painted_stars = u"\u2605" * star_number
    # Uncomment this to display unearned stars as empty
    # unpainted_stars = u"\u2606" * (5 - star_number)
    stars = painted_stars # + unpainted_stars
    return stars


def download_images(products, image_path='./data/facebook/'):
    """
    Download images given the products information and local image path.
    For creating carousel ads purpose, we need the images, and the local path to upload them.
    In order to make images be identified easily, we change the image name after downloading.
    :param products: A list of products
    :param image_path:A string of path
    :return:
    """
    st_directory = image_path
    if not os.path.exists(image_path):
        os.makedirs(image_path)
    for x in products:
        product_types = [t.strip() for t in x['product_type'].split('&')]
        types = '&'.join(x for x in product_types)
        product_type = types.lower().replace(' ', '-').replace('/', '-')
        product_id = x['entity_id']
        st_image_url = x.get('image')
        img_name = st_image_url.split('/')[-1]
        image_path = os.path.join(st_directory, img_name)
        urllib.urlretrieve(st_image_url, image_path)
        x['local_image'] = image_path
        color = str(x.get('color', '#6F4AB3'))
        star_color = str(x.get('star_color', '#FFAB00'))
        # Add rectangle badge for 'Shop Now'

        # Define sizes for relative overlay
        img = Image.open(image_path)
        w, h = img.size

        if x['add_shop_now']:
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype('./modjento/static/fonts/urw_neuzeitgrotesktot-bol-webfont.ttf', 56)
            shop_w, shop_h = draw.textsize('SHOP NOW', font)

            try:
                draw.rectangle([(((w - shop_w) // 2) - 30, h - shop_h - 280), ((w - shop_w) // 2 + shop_w + 30, h - shop_h - 165 )], fill=color)
            except ValueError, ex:
                logger.exception(msg='Please type in a right color code: %s' % ex)
                return

            draw.text(((w - shop_w) // 2, h - shop_h - 250), 'SHOP NOW', (254,254,254), font=font)

            new_path = os.path.join(st_directory, 'x%s_%sx.jpg' % (product_type, product_id))
            img.save(new_path)
            x['local_image'] = new_path

        if x['add_banner']:
            new_path = x['local_image']
            img = Image.open(new_path)
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype('./modjento/static/fonts/FreightSansProBook-Regular_gdi.ttf', 50)
            # Add a radiant-orchid triangle on the upper-left corner of the image
            try:
                draw.polygon([(0, 0), (0, 250), (250, 0)], fill=color)
            except ValueError, ex:
                logger.exception(msg='Please type in a right color code: %s' % ex)
                return
            rg_percentages = x['percentage'].split('\n')
            draw.text((14, 30), rg_percentages[0], (255, 255, 255), font=font)
            draw.text((14, 80), rg_percentages[1], (255, 255, 255), font=font)
            new_path = os.path.join(st_directory, 'x%s_%sx.jpg' % (product_type, product_id))
            img.save(new_path)
            x['local_image'] = new_path

        if x['show_stars']:
            new_path = x['local_image']
            stars = get_stars(x)
            img = Image.open(new_path)
            draw = ImageDraw.Draw(img)
            w, h = img.size
            font = ImageFont.truetype('./modjento/static/fonts/DejaVuSans-Bold.ttf', 130)
            text_w, text_h = draw.textsize(stars, font)
            draw.text(((w - text_w) // 2, h - text_h - 40), stars, fill=star_color, font=font)
            new_path = os.path.join(st_directory, 'x%s_%sx.jpg' % (product_type, product_id))
            img.save(new_path)
            x['local_image'] = new_path


def shopify_download_images(products, image_path='./data/facebook/'):
    """
    Download images given the products information and local image path.
    For creating carousel ads purpose, we need the images, and the local path to upload them.
    In order to make images be identified easily, we change the image name after downloading.
    :param products: A list of products
    :param image_path:A string of path
    :return:
    """
    st_directory = image_path
    if not os.path.exists(image_path):
        os.makedirs(image_path)
    for x in products:
        st_image_url = x.get('image')
        img_name = st_image_url.split('/')[-1].split('?')[0]
        image_path = os.path.join(st_directory, img_name)
        urllib.urlretrieve(st_image_url, image_path)
        x['local_image'] = image_path


def get_bmc_link(bmc_id=None):
    """
    get the brand model category given the category id
    For seo purposes, we want to have the phone brand and phone model with the category id
    we can add the brand information to the product url
    :param bmc_id: brand model category id
    :return: product url
    """
    if not bmc_id:
        return ''
    if isinstance(bmc_id, str):
        bmc_id = int(bmc_id)
    bmc_link = EavAttribute.objects.get_values(
        entity_ids=[bmc_id],
        entity_type=3,
        field_names=['url_path'],
        json_values=False,
        store_id=[1, 2, 3])
    return bmc_link[bmc_id]['url_path'].replace('.html', '')


def get_product_link(url):
    """
    Get product link give url_key of a product
    This function is used to get the product link so that
    users can see the whole product info after they hit the url
    :param url: url key
    :return: product link
    """
    if not url: return ''
    st_format = '%s%s' if url[0] == '/' else '%s/%s'
    st_url = st_format % ('http://www.cellularoutfitter.com', url,)
    return st_url


def generate_tracking_tag(campaign_name):
    campaign_name = re.sub(r'[^A-Za-z0-9\._\-]', '-', campaign_name)
    return 'DZID=Facebook_OCPM_%s&utm_source=facebook&utm_medium=ocpm&utm_campaign=%s' % (
        campaign_name, campaign_name)


def get_image_url(image):
    """
    Get the image link given image key
    :param image: image key
    :return: image link
    """
    if not image:
        return image
    if image.startswith('URL/'):
        image = image.replace('URL', 'http://cellularoutfitter.com/media/catalog/product')
    else:
        image = 'http://cellularoutfitter.com/media/catalog/product/%s' % (image,)
    return image


def upload_images(products, fb_credentials):
    """
    Given a list of products, upload their images ad catch images hashes
    For creating carousel ads purpose, we need to upload products images and catch their hashes to track products
    :param products: A list of products
    :return: Nothing
    """
    fb = FacebookConnect(**fb_credentials)
    for x in products:
        local_image = x.get('local_image')
        logger.info('Uploading image [%s]', local_image)
        if local_image:
            try:
                img_hash = fb.upload_image(local_image)
                logger.info('Image upload successfule')
                x['image_hash'] = img_hash
            except FacebookRequestError, ex:
                logger.exception('Facebook error to upload image: %s', ex, extra={
                    'user_access_token': fb.user_token
                })
        logger.info('All done!')


def create_carousel_ad(fb_credentials, ad_message, products, ad_set_id=None, ad_name=None, ad_is_active=False,
                       ad_link='http://www.cellularoutfitter.com',
                       ad_caption='http://www.cellularoutfitter.com'):
    """
    Create a carousel ad given products and ad information

    :param ad_message: A string of top-level ad message
    :param products: A list of products
    :param ad_set_id: A String of set id, optional argument
    :param ad_name: A String of unique ad name
    :param ad_link: A string
    :param ad_caption: A url
    :param ad_is_active: A Boolean
    :return:nothing
    """
    fb = FacebookConnect(**fb_credentials)
    link = LinkData()
    link[link.Field.multi_share_optimized] = True
    link[link.Field.link] = ad_link
    link[link.Field.message] = ad_message
    link[link.Field.child_attachments] = list()
    for x in products:
        product = AttachmentData()
        product[AttachmentData.Field.link] = x['link']
        product[AttachmentData.Field.name] = x['name']
        product[AttachmentData.Field.description] = x['description']
        product[AttachmentData.Field.image_hash] = x['image_hash']
        product[AttachmentData.Field.call_to_action] = {'type': 'SHOP_NOW' }
        link[link.Field.child_attachments].append(product)
        print x['link']
    link[link.Field.caption] = ad_caption
    p_creative = fb.create_carousel_ad(link)
    if ad_set_id and ad_name:
        new_ad = fb.create_ad(ad_set_id, ad_name, ad_is_active, p_creative)
        return new_ad
    return p_creative


def add_tracking(url, campaign_name, ad_set, item_id=None):
    """
    Get tracking link given url and campaign name
    :param url: A string of url prefix, ex: 'Http://www/cellularoutfitter.com'
    :param campaign_name: A string of campaign_name, ex:'CO'
    :return: A string of tracking url
    """
    if not campaign_name:
        return url
    campaign_name = re.sub(r'[^A-Za-z0-9\._\-]', '-', campaign_name)
    param = '&'
    if not '?' in url:
        param = '?'
    if item_id:
        return '%s%sDZID=Facebook_OCPM_%s_%s_%s_&utm_source=facebook&utm_medium=ocpm&utm_campaign=%s' % (
            url, param, campaign_name, item_id, ad_set, campaign_name
        )
    return '%s%sDZID=Facebook_OCPM_%s_seemore_%s_&utm_source=facebook&utm_medium=ocpm&utm_campaign=%s' % (
            url, param, campaign_name, ad_set, campaign_name
        )


def generate_url_prefix(bmc_id):
    """
    Get the url prefix given brand model category id
    :param bmc_id: A string of brand model category id
    :return: A string of url prefix
    """
    if not bmc_id:
        return settings.MAGENTO_URL_PREFIXES['pdp']
    else:
        url_info = EavAttribute.objects.get_values(
                entity_ids=[bmc_id],
                entity_type=3,
                field_names=['url_path']
        )
        if not url_info:
            return settings.MAGENTO_URL_PREFIXES['pdp']
        return '%s%s' % (settings.MAGENTO_URL_PREFIXES['pdp'], url_info[bmc_id]['url_path'])


def pull_product_info(product_ids, campaign_name=None, ad_set_name=None, category_id=None):
    """
    Get all the products info given a list of product ids
    To create carousel ads, we need the images, links, prices of the products, and we pull them from the db.
    :param product_ids: A list of product ids
    :param campaign_name: A string of campaign name, optional argument
    :param ad_set_name: A String od ad_set_name
    :param category_id: A String od category_id
    :return: A list of products
    """
    products = []
    product_ids = map(int, product_ids)
    rg_fields = [ 'name', 'image', 'product_type',
                  'price', 'special_price', 'msrp',
                  'special_from_date', 'special_to_date',
                  'url_path', 'url_key', ]
    mp_values = EavAttribute.objects.get_values(
        product_ids,
        entity_type=4,
        field_names=rg_fields,
        json_values=False)

    product_stock = list(CataloginventoryStockItem.objects.filter(product_id__in=product_ids).only(
        'product_id',
        'qty'
    ))

    for item in product_stock:
        mp_values[item.product_id].update({
            'qty': int(item.qty)
        })

    st_url_prefix = generate_url_prefix(category_id)
    if st_url_prefix[-5:] == '.html': st_url_prefix = st_url_prefix.replace('.html', '')
    if st_url_prefix[-1] != '/': st_url_prefix += '/'

    # Maintain original order of product IDs
    mp_products = CatalogProductEntity.objects.in_bulk(product_ids)
    rg_products = [ mp_products[x] for x in product_ids ]
    del mp_products

    # Load the review summary
    mp_reviews = {}
    reviews = ReviewEntitySummary.objects.filter(store_id=2, entity_pk_value__in=product_ids).values_list(
        'entity_pk_value', 'rating_summary', 'reviews_count'
    )
    for product_id, rating_summary, reviews_count in reviews:
        mp_reviews[product_id] = (rating_summary, reviews_count)
    # Load the media gallery
    rg_image_data = MediaGalleryValue.objects.select_related('value').filter(
        value__entity_id__in=product_ids,
        disabled=False
    ).order_by(
        'position'
    ).values_list('value__entity_id', 'value__value')
    mp_images = defaultdict(list)
    for x in rg_products:
        n_id = x.entity_id
        data = mp_values.get(n_id, {})
        if data.get('image'):
            mp_images[n_id].append(settings.MAGENTO_URL_PREFIXES['img'] + data['image'])
    for n_id, value in rg_image_data:
        st_image = settings.MAGENTO_URL_PREFIXES['img'] + value
        if st_image not in mp_images[n_id]:
            mp_images[n_id].append(st_image)
    # Create the response dictionary
    for x in rg_products:
        n_id = x.entity_id
        data = mp_values.get(n_id, {})
        st_url = st_url_prefix + data['url_path']
        review_values = mp_reviews.get(n_id, (0, 0))
        rating_summary = normalize_summary(review_values[0])
        reviews_count = review_values[1]
        mp_product = {
            'entity_id': n_id,
            'name': data.get('name', ''),
            'sku': x.sku,
            'image': settings.MAGENTO_URL_PREFIXES['img'] + data.get('image') if data.get('image') else None,
            'images': mp_images.get(n_id, []),
            'link': add_tracking(st_url, campaign_name, ad_set_name, n_id),
            'product_type': data.get('product_type', ''),
            'rating_summary':rating_summary ,
            'reviews_count': reviews_count,
            'qty': data.get('qty', 0)
        }

        d_special_price = data.get('special_price')
        dt_now = pytz.utc.localize(datetime.now())
        dt_from = data.get('special_from_date')
        dt_to = data.get('special_to_date')
        if d_special_price and (
                not dt_from or dt_from <= dt_now) or (
                not dt_to or dt_to >= dt_now):
            mp_product['sale_price'] = '$%.2f' % d_special_price
            mp_product['retail_price'] = '$%.2f' % data['price']
            mp_product['save'] = '$%.2f' % (data['price'] - d_special_price,)
            mp_product['percentage'] = 'SAVE\n%d%%' % (100 - d_special_price / data['price'] * 100,)
        else:
            mp_product['sale_price'] = '$%.2f' % data['price']
            mp_product['retail_price'] = '$%.2f' % data['price']
            mp_product['save'] = ''
            mp_product['percentage'] = ''
        products.append(mp_product)
    return products


def normalize_summary(rating_summary):
    if rating_summary:
        rating_summary = round((rating_summary / 20), 1)
    return rating_summary


def generate_collection_url_prefix_shopify(handle):
    """
    Get the collection url prefix given collection handle
    :param handle: A string of collection handle
    :return: A string of url prefix
    """
    if not handle:
        return settings.SHOPIFY_URL_PREFIXES['pdp']
    else:
        return '%scollections/%s' % (settings.SHOPIFY_URL_PREFIXES['pdp'], handle)


def generate_variant_url_prefix_shopify(collection_handle, product_handle, variant_id):
    """
    Get the variant url prefix given collection handle, product handle and variant id
    :param collection_handle: A string of collection handle
    :param product_handle: A string of product handle
    :param variant_id: A string of variand id
    :return: A string of url prefix
    """
    return ('%scollections/%s/products/%s?variant=%s' %
            (settings.SHOPIFY_URL_PREFIXES['pdp'], collection_handle,
             product_handle, variant_id))


def pull_product_variant_info_shopify(sku_ids, campaign_name=None, ad_set_name=None, handle=None):
    """
    Get all the product variant info given a list of sku ids
    To create carousel ads, we need the images, links, prices of the product variants, and we pull them from the db.
    :param sku_ids: A list of sku ids
    :param campaign_name: A string of campaign name, optional argument
    :param ad_set_name: A String od ad_set_name
    :param handle: A String of handle
    :return: A list of products
    """
    skus = []
    variants = ProductVariant.objects.filter(sku__in=sku_ids)

    # Create the response dictionary
    for variant in variants:
        st_url = generate_variant_url_prefix_shopify(handle,
                                                     variant.product.handle,
                                                     variant.variant_id)
        name = '%s - %s' % (variant.product.title, variant.title)
        description = 'Sale Price %s | Retail Price %s' % (variant.price,
                                                           variant.compare_at_price)

        mp_variant = {
            'entity_id': variant.variant_id,
            'name': name,
            'sku': variant.sku,
            'image': variant.image.src if variant.image else None,
            'images': list(variant.productimage_set.all().values_list('src', flat=True)),
            'link': add_tracking(st_url, campaign_name, ad_set_name, variant.variant_id),
            'description': description,
            'qty': variant.inventory_quantity
        }

        skus.append(mp_variant)
    return skus
