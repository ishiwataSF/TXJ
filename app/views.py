from django.db import transaction

from django.urls import reverse
from django.views.generic import ListView, DetailView, TemplateView, UpdateView, CreateView
from .models import Staff, Customer, GeneratedData, MatchedData, VisuallyMachedData, ImportData
from .forms import CustomerSelectForm, UploadFileSelectForm
import openpyxl



class GeneratedDataCreateView(CreateView):
    model = GeneratedData
    form_class = CustomerSelectForm
    template_name = 'app/customer_select.html'

    @transaction.atomic
    def form_valid(self, form):
        post = form.save(commit=False)
        author = Staff.objects.get(author=self.request.user)
        post.author = author
        post.status = 0
        post.save()

        return super().form_valid(form)

    def get_success_url(self):
        link = reverse('upload')
        pk = self.object.pk
        link = f'{link}?generated_data={pk}'
        # return reverse('upload')
        return link


class MatchedDataCreateView(CreateView):
    model = MatchedData
    template_name = 'app/upload.html'
    form_class = UploadFileSelectForm

    @transaction.atomic
    def form_valid(self, form):
        post = form.save(commit=False)
        author = Staff.objects.get(author=self.request.user)
        post.author = author
        generated_data_pk = self.request.GET.get('generated_data')
        post.generated_id = generated_data_pk
        generated_data = GeneratedData.objects.filter(pk=generated_data_pk)
        post.generated = GeneratedData.objects.filter(status__contains=0).last()
        post.save()

        generated = GeneratedData.objects.filter(status__contains=0).last()
        generated.status = 1
        generated.save()

        return super().form_valid(form)


    def get_success_url(self):
        link = reverse('download')
        pk = self.object.pk
        link = f'{link}?matched_data={pk}'

        return link

        # return reverse('download')

class MatchedDataUpdateView(TemplateView):
    model = MatchedData
    template_name = 'app/csv_download.html'

    def crate_csv(self):
        matched = MatchedData.objects.last()
        context = {
            'upload_url' : matched.brycen_file.url ,
        }

        return context
        # matched.billing_file.url

















    









