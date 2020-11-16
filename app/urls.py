from django.conf import settings
from django.contrib.staticfiles.urls import static
from django.urls import path
from .views import HistoryListView, GeneratedDataCreateView, MatchedDataCreateView, VisuallyMatchedDataCreateView, \
    ImportDataCreateView, MatchedDataDetailView, ImportDataDetailView, LoginFormView, CustomerSelectAndFileUpLoadView, \
    MatchedDataDetailAndVisuallyMatchedDataCreateView, MatchedDataCheckProcedureTmprateView

urlpatterns = [
    path('', LoginFormView.as_view(), name='login'),
    path('top/', HistoryListView.as_view(), name='top'),
    path('file_upload/', CustomerSelectAndFileUpLoadView.as_view(), name='file_upload'),
    path('matched_data/<int:pk>/detail_and_create',MatchedDataDetailAndVisuallyMatchedDataCreateView.as_view(), name='detail_and_create'),
    path('check_procedure/',MatchedDataCheckProcedureTmprateView.as_view(), name='check_procedure'),
    path('customer_select/', GeneratedDataCreateView.as_view(), name='customer_select'),
    path('generated-data/<int:pk>/upload/', MatchedDataCreateView.as_view(), name='upload'),
    path('matched_data/<int:pk>/',MatchedDataDetailView.as_view(), name='matched_data_detail'),
    path('matched_data/<int:pk>/visually_match/', VisuallyMatchedDataCreateView.as_view(), name='visually_match'),
    path('visually_match/<int:pk>/import_data/', ImportDataCreateView.as_view(), name='import_data'),
    path('import_data/<int:pk>/', ImportDataDetailView.as_view(), name='import_data_detail'),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)