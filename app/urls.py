from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import static
from django.urls import path
from .views import GeneratedDataCreateView, MatchedDataCreateView, MatchedDataUpdateView

urlpatterns = [
    path('', GeneratedDataCreateView.as_view(), name='customer_select'),
    path('upload/', MatchedDataCreateView.as_view(), name='upload'),
    path('upload/download', MatchedDataUpdateView.as_view(), name='download'),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)