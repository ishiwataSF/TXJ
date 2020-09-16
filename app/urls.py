from django.urls import path
from .views import GeneratedDataCreateView

urlpatterns = [
    path('', GeneratedDataCreateView.as_view(), name='upload')
]