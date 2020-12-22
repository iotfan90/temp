import csv

from collections import OrderedDict

from mobovidata_dj.analytics.models import Customer
from mobovidata_dj.responsys.utils import ResponsysApi
from modjento.models import SalesFlatOrder, SalesFlatOrderAddress


def compile_customer_data():
    """
    Compile customer data Zaius requires for their CSV imports
    """

    # Number of customer QuerySets to fetch in initial query
    BATCH_SIZE = 1000

    """
    Master data dictionary to be used to store customer data
    data.keys() should return
        ['uuid', 'emails', 'first_names', 'last_names', 'phone_numbers',
         'street', 'city', 'state', 'zip', 'countries']
    """
    data = {}

    # QuerySet from Customer table in mobovidata_www database
    qs_uuid = Customer.objects.filter(riid__isnull=False)[:BATCH_SIZE]

    # RIID's for each customer in QuerySet
    riids = [uuid.riid for uuid in qs_uuid]

    # Emails of each Customer from RIID's using Responsys
    emails = []
    for riid in riids:
        emails.append(str(ResponsysApi().get_email_from_riid(riid)))

    data['uuid'] = [str(x.uuid) for x in qs_uuid]
    data['emails'] = emails

    # Data collected from SalesFlatOrder (sfo) table
    first_and_last = data_from_sfo(emails)
    data['first_names'] = first_and_last[0]
    data['last_names'] = first_and_last[1]

    # Data collected from SalesFlatOrderAddress
    address_data = data_from_sfoa(emails)
    data['phone_number'] = address_data['phone']
    data['street'] = address_data['street']
    data['city'] = address_data['city']
    data['state'] = address_data['state']
    data['zipcode'] = address_data['zipcode']
    data['country'] = address_data['country']

    return customer_data2csv(data)


def customer_data2csv(data_dict):
    """
    Creates CSV from customer information:
    data_dict : dictionary of arrays containing customer information
    """
    # Organizes dictionary into OrderedDict so as to retain sort
    customer_data = OrderedDict([
        ('customer_id', data_dict['uuid']),
        ('email', data_dict['emails']),
        ('first_name', data_dict['first_names']),
        ('last_name', data_dict['last_names']),
        ('phone', data_dict['phone_numbers']),
        ('street1', data_dict['street']),
        ('city', data_dict['city']),
        ('state', data_dict['state']),
        ('zip', data_dict['zip']),
        ('country', data_dict['countries']),
    ])

    # Create CSV and feed it customer information row by row
    with open('zaius_customer.csv', 'wb') as csvfile:
        fieldnames = [x for x in customer_data]
        writer = csv.writer(csvfile)
        writer.writerow([key for key in customer_data])
        index = 0
        for each in range(len(customer_data['customer_id'])):
            row = []
            for x in customer_data:
                row.append(customer_data[x][index])
            writer.writerow(row)
            index += 1
    csvfile.close()

    return True


def data_from_sfo(emails):
    """
    Gather following data from SalesFlatOrder (sfo) table:
    first names, last names
    """
    master_data = []
    for email in emails:
        qs = SalesFlatOrder.objects.filter(customer_email=email)
        master_data.append(qs)
    fn = []
    ln = []
    for x in master_data:
        if not len(x):
            fn.append('')
            ln.append('')
            continue
        else:
            fn.append(str(getattr(x[0], 'customer_firstname')))
            ln.append(str(getattr(x[0], 'customer_lastname')))

    return fn, ln


def data_from_sfoa(emails):
    """
    Gather following data from SalesFlatOrderAddress (sfoa) table:
    phone numbers, street addresses, cities, states, zipcodes, countries
    """
    master_address_data = []
    for email in emails:
        qs = SalesFlatOrderAddress.objects.filter(email=email,
                                                  address_type='billing')
        master_address_data.append(qs)

    zaius_sfoa_data = {
        'phone': [],
        'street': [],
        'city': [],
        'state': [],
        'zipcode': [],
        'country': [],
    }

    for x in master_address_data:
        if not len(x):
            for x in zaius_sfoa_data.keys():
                zaius_sfoa_data[x].append('')
            continue
        else:
            zaius_sfoa_data['phone'].append(str(getattr(x[0], 'telephone')))
            zaius_sfoa_data['street'].append(str(getattr(x[0], 'street')))
            zaius_sfoa_data['city'].append(str(getattr(x[0], 'city')))
            zaius_sfoa_data['state'].append(str(getattr(x[0], 'region')))
            zaius_sfoa_data['zipcode'].append(str(getattr(x[0], 'postcode')))
            zaius_sfoa_data['country'].append(str(getattr(x[0], 'country_id')))

    return zaius_sfoa_data
