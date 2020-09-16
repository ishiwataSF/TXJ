from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.views.generic import ListView, DetailView, TemplateView, UpdateView, CreateView
from .models import Staff, Customer, GenerateData, MatchedData, VisuallyMachedData, ImportData
from .forms import CustomerSelectForm, UploadFileSelectForm

class GeneratedDataCreateView(CreateView):
    model = GenerateData
    template_name = 'app/upload.html'
    form_class = CustomerSelectForm

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        post.status = 1
        post.save()

        return super().form_valid(form)

class MatchedDataCreateView(CreateView):
    model = MatchedData
    template_name = 'app/upload.html'
    form_class = UploadFileSelectForm

    def form_valid(self, form):
        post = form.save(commit=False)
        post.brycen_file()
        post.billing_file()
        post.save()

        return super().form_valid(form)
