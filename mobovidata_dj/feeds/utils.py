from django.conf import settings


def map_facebook_feed(row, fb_rows, idx, errors):
    """
    Map default column names to Facebook specific column names
    @param dict row: raw product feed data
    @param list fb_rows: Facebook column name mapped rows
    @param int idx: enumerator
    @param list errors: faulty rows
    @return void
    """
    facebook_row = {v: row[k] for k, v in
                    settings.FACEBOOK_COLUMN_MAP.iteritems()}
    try:
        facebook_row['sale_price'] = '%s USD' % round(
            float(facebook_row['sale_price']), 2)
        facebook_row['price'] = '%s USD' % round(float(facebook_row['price']),
                                                 2)
        facebook_row['availability'] = 'in stock'
        if int(facebook_row['inventory']) == 0:
            facebook_row['availability'] = 'out of stock'
        tracking = settings.FACEBOOK_FEED['tracking_string'] % row['id']
        facebook_row['link'] = '%s%s' % (row['link'].split('?')[0], tracking)
        if len(row['title']) > 150:
            facebook_row['title'] = row['title'][:150]
        if row['description'] == '':
            facebook_row[
                'description'] = ('Top quality %s at the lowest price online!' %
                                  facebook_row['title'])
        fb_rows.append(facebook_row)
    except:
        errors.append([row, idx])
