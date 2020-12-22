from django import forms

from .models import Dojomojo, Unbounce


class DojomojoModelForm(forms.ModelForm):
    class Meta:
        model = Dojomojo
        exclude = ('status',)


class UnbounceModelForm(forms.ModelForm):
    class Meta:
        model = Unbounce
        exclude = ('status', 'date_processed',)
