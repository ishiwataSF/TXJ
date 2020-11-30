from django.conf import settings
from django.contrib.staticfiles.urls import static
from django.urls import path
from .views import HistoryListView, ImportDataCreateView, ImportDataDetailView, \
    LoginFormView, CustomerSelectAndFileUpLoadView,MatchedDataDetailAndVisuallyMatchedDataCreateView, MatchedDataCheckProcedureTmprateView, logout

urlpatterns = [
    path('accounts/login/', LoginFormView.as_view(), name='login'),
    path('accounts/logout/',logout, name='logout'),
    path('', HistoryListView.as_view(), name='top'),
    path('file_upload/', CustomerSelectAndFileUpLoadView.as_view(), name='file_upload'),
    path('matched_data/<int:pk>/detail_and_create',MatchedDataDetailAndVisuallyMatchedDataCreateView.as_view(), name='detail_and_create'),
    path('check_procedure/',MatchedDataCheckProcedureTmprateView.as_view(), name='check_procedure'),
    path('visually_match/<int:pk>/import_data/', ImportDataCreateView.as_view(), name='import_data'),
    path('import_data/<int:pk>/', ImportDataDetailView.as_view(), name='import_data_detail'),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)