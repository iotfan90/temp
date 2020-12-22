from mobovidata_dj.analytics.models import Customer, CustomerLifecycleTracking


def create_customer_with_cart():
    customer = Customer.objects.create_customer(riid=274399105)
    (CustomerLifecycleTracking.objects
     .set_lifecycle_stage_to_cart(2056304, customer=customer))
    return customer

