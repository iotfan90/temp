from django import forms
from .models import MasterAttributeSet


class ModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)
        widget = self.fields['categories'].widget
        choices = []
        m = MasterAttributeSet.objects.filter(attribute_set_url__isnull=False)
        for choice in m:
            choices.append((choice.id, choice.attribute_set_name))
        widget.choices = choices
