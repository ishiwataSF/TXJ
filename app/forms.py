from betterforms.multiform import MultiModelForm
from django import forms
from django.forms import modelformset_factory
from django.core.exceptions import ValidationError
from .models import GeneratedData, MatchedData, VisuallyMatchedData, ImportData, BillingData, Place


class CustomerSelectForm(forms.ModelForm):

    class Meta:
        model = GeneratedData
        fields = ('customer', )
        labels = {'customer': '取引先選択'}
        widgets = {'customer': forms.Select(attrs={'class': 'customer-select-form'})}


class UploadFileSelectForm(forms.ModelForm):

    class Meta:
        model = MatchedData
        fields = ('brycen_file', 'billing_file', )
        labels = {'brycen_file': 'ブライセン契約データ',
                  'billing_file': '電子データ'}
        widgets = {'brycen_file': forms.FileInput(attrs={'accept': '.xlsx'}),
                   'billing_file': forms.FileInput(attrs={'accept': '.csv'})}

class BiilingFileUploadFrom(forms.ModelForm):
    def is_valid(self):
        valid = super().is_valid()
        if valid and self.cleaned_data['billing_file'] is None:
            e = ValidationError('ファイルを選択してください')
            self.add_error('billing_file', e)
            return False
        return valid

    class Meta:
        model = MatchedData
        fields = ('billing_file', )
        widgets = {'billing_file': forms.FileInput(attrs={'accept': '.csv'})}


class VisuallyMatchedDataCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['created_date'].widget.attrs['readonly'] = 'readonly'
        self.fields['created_date'].help_text = '※日付は編集不可です。'

    class Meta:
        model = VisuallyMatchedData
        fields = ('created_date', )


class ImportDataCreateForm(forms.ModelForm):
    def __init__(self, *args, method='GET', upload_and_create=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._upload_and_create = upload_and_create
        #self._create = create
        if method =='POST' and not upload_and_create:
            del self.fields['visually_matched_file']
        # print('self._upload_and_create:{}'.format(self._upload_and_create))
        # print('self._create:{}'.format(self._create))

    def is_valid(self):
        valid = super().is_valid()
        if valid and self._upload_and_create and self.cleaned_data['visually_matched_file'] is None:
            e = ValidationError('ファイルを選択してください')
            self.add_error('visually_matched_file', e)

            return False

        #elif valid and self._create and self.cleaned_data['visually_matched_file']:
            #self.cleaned_data['visually_matched_file'] = ''
            #print(valid)
            #return valid
            #e = ValidationError('ファイルを選択したまま、インポートデータ作成を押さないでください')
            #self.add_error('visually_matched_file', e)

            #return False

        return valid

    class Meta:
        model = ImportData
        fields = ('visually_matched_file', )
        widgets = {'visually_matched_file': forms.FileInput(attrs={'accept': '.csv'})}


class CustomerSelectAndFileUpLoadMultiFrom(MultiModelForm):
    form_classes = {'generated_data': CustomerSelectForm,
                    'matched_data': UploadFileSelectForm}


    def save(self, commit=True):
        objects = super(CustomerSelectAndFileUpLoadMultiFrom, self).save(commit=False)

        if commit:
            generated_data = objects['generated_data']
            generated_data.save()
            matched_data = objects['matched_data']
            matched_data.save()

            return objects


class BillingDataFrom(forms.ModelForm):

    def __init__(self, queryset=None, customer_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if customer_id:
            self.fields['place'].queryset = Place.objects.filter(customer_id=customer_id)

    class Meta:
        model = BillingData
        fields = ('billing_date', 'agent', 'product', 'place', 'item', 'amount', 'unit', 'unit_price', 'total', )
        widgets = {'billing_date': forms.TextInput(attrs={'class': 'billing-data-date-form form-control','type': 'date', 'required': 'required'}),
                   'amount': forms.NumberInput(attrs={'class': 'billing-data-amount-form form-control', 'required': 'required'}),
                   'unit_price': forms.NumberInput(attrs={'class': 'billing-data-unit_price-form form-control', 'required': 'required'}),
                   'total': forms.NumberInput(attrs={'class': 'billing-data-total-form form-control', 'required': 'required'}),
                   'agent': forms.widgets.Select(attrs={'class': 'billing-agent-form form-control', 'required': 'required'}),
                   'product': forms.Select(attrs={'class': 'billing-product-form form-control', 'required': 'required'}),
                   'place': forms.Select(attrs={'class': 'billing-place-form form-control', 'required': 'required'}),
                   'item': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
                   'unit': forms.Select(attrs={'class': 'form-control', 'required': 'required'})}


BillingDataFromSet = modelformset_factory(
    BillingData, form=BillingDataFrom, exclude=('create_date', 'staff', ), extra=1, can_delete=True)








