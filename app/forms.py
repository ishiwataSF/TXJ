from django import forms

from .models import GeneratedData, MatchedData, VisuallyMatchedData, ImportData


class CustomerSelectForm(forms.ModelForm):

    class Meta:
        model = GeneratedData
        fields = ('customer', )


class UploadFileSelectForm(forms.ModelForm):

    class Meta:
        model = MatchedData
        fields = ('brycen_file', 'billing_file', )

class VisuallyMatchedDataCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['created_date'].widget.attrs['readonly'] = 'readonly'
        self.fields['created_date'].help_text = '※日付は編集不可です。'

    class Meta:
        model = VisuallyMatchedData
        fields = ('created_date', )

class ImportDataCreateForm(forms.ModelForm):

    class Meta:
        model = ImportData
        fields = ('visually_matched_file', )








