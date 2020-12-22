from django import forms


class BrowseEventForm(forms.Form):
    RIID_ = forms.IntegerField()
    PRODUCTS = forms.CharField()
    BRAND_NAME = forms.CharField(required=False)
    MODEL_NAME = forms.CharField(required=False)
    BMC_ID = forms.CharField(required=False)
    STRANDS_UID = forms.CharField(required=False)


class CartEventForm(forms.Form):
    RIID_ = forms.IntegerField()
    STRANDS_UID = forms.CharField(required=False)
    QUOTE_ID = forms.CharField()
    CART_PRODUCTS = forms.CharField(required=False)
    BRAND_NAME = forms.CharField(required=False)
    MODEL_NAME = forms.CharField(required=False)


class ProductViewForm(forms.Form):
    product_id = forms.CharField()


class TrackingForm(forms.Form):
    VIEW_CHOICES = (
        ('pv', 'PageView'),
        ('cr', 'Cart'),
        ('or', 'Order'),
    )
    mvapi = forms.CharField(max_length=2,
                            widget=forms.Select(choices=VIEW_CHOICES))
    mvrid = forms.CharField(required=False)
    mvid = forms.CharField(required=False)
    mvsid = forms.CharField(required=False)
    mvhdrs = forms.CharField(required=False)

    mvt = forms.CharField(required=False)
    mvpt = forms.CharField(required=False)
    mvsl = forms.CharField(required=False)
    mvprm = forms.CharField(required=False)
    mvpid = forms.CharField(required=False)
    mvst = forms.CharField(required=False)
    mvdv = forms.CharField(required=False)

    mvcid = forms.CharField(required=False)
    mvoid = forms.CharField(required=False)
    strandsid = forms.CharField(required=False)
