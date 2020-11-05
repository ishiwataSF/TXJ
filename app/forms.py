from django import forms
from django.core.exceptions import ValidationError
from .models import GeneratedData, MatchedData, VisuallyMatchedData, ImportData


class CustomerSelectForm(forms.ModelForm):

    class Meta:
        model = GeneratedData
        fields = ('customer', )


class UploadFileSelectForm(forms.ModelForm):

    class Meta:
        model = MatchedData
        fields = ('brycen_file', 'billing_file', )
        widgets = {'brycen_file': forms.FileInput(attrs={'accept': '.xlsx'}),
                   'billing_file': forms.FileInput(attrs={'accept': '.csv'})}

class VisuallyMatchedDataCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['created_date'].widget.attrs['readonly'] = 'readonly'
        self.fields['created_date'].help_text = '※日付は編集不可です。'

    class Meta:
        model = VisuallyMatchedData
        fields = ('created_date', )

class ImportDataCreateForm(forms.ModelForm):
    def __init__(self, *args, upload_and_create=False, create=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._upload_and_create = upload_and_create
        self._create = create
        # print('self._upload_and_create:{}'.format(self._upload_and_create))
        # print('self._create:{}'.format(self._create))

    def is_valid(self):
        valid = super().is_valid()
        if valid and self._upload_and_create and self.cleaned_data['visually_matched_file'] is None:
            e = ValidationError('ファイルを選択してください')
            self.add_error('visually_matched_file', e)

            return False

        elif valid and self._create and self.cleaned_data['visually_matched_file']:
            e = ValidationError('ファイルを選択したまま、インポートデータ作成を押さないでください')
            self.add_error('visually_matched_file', e)

            return False

        return valid

    class Meta:
        model = ImportData
        fields = ('visually_matched_file', )
        widgets = {'visually_matched_file': forms.FileInput(attrs={'accept': '.csv'})}









