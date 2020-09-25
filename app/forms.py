from django import forms

from .models import GeneratedData, MatchedData
from django.core.files.storage import default_storage

class CustomerSelectForm(forms.ModelForm):

    class Meta:
        model = GeneratedData
        fields = ('customer', )


class UploadFileSelectForm(forms.ModelForm):

    class Meta:
        model = MatchedData
        fields = ('brycen_file', 'billing_file', 'created_file', )

