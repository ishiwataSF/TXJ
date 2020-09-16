from django import forms

from .models import GenerateData, MatchedData

class CustomerSelectForm(forms.ModelForm):

    class Meta:
        model = GenerateData
        fields = ('customer', )

class UploadFileSelectForm(forms.ModelForm):

    class Meta:
        model = MatchedData
        fields = ('brycen_file', 'billing_file', )