# coding: utf-8

from __future__ import unicode_literals
from django.forms import ModelForm, BooleanField
from tinymce.widgets import TinyMCE
from .models import DossierDEvenements


class DossierDEvenementsForm(ModelForm):
    statique = BooleanField(required=False)

    class Meta(object):
        model = DossierDEvenements
        widgets = {
            'contenu': TinyMCE,
        }

    class Media(object):
        css = {
            'all': ('css/custom_admin.css',),
        }

    def __init__(self, *args, **kwargs):
        if 'instance' in kwargs:
            initial = kwargs.get('initial', {})
            initial['statique'] = kwargs['instance'].evenements.exists()
            kwargs['initial'] = initial
        super(DossierDEvenementsForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(DossierDEvenementsForm, self).clean()
        if cleaned_data['statique']:
            cleaned_data['evenements'] = self.instance.get_queryset()
            self.instance.evenements.add(*cleaned_data['evenements'])
            for k in ('debut', 'fin', 'lieux', 'oeuvres', 'auteurs',
                      'circonstance'):
                del cleaned_data[k]
        return cleaned_data
