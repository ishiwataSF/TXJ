from django.conf import settings
from django.contrib.staticfiles.urls import static
from django.urls import path
from .views import HistoryListView, ImportDataCreateView, ImportDataDetailView, \
    LoginFormView, MatchedDataDetailAndVisuallyMatchedDataCreateView, logout,\
    BillingDataCreateView, CustomerSelectAndBrycenFileUpLoadView, SelectFileOrBillingDataFormView, BillingDataDetailView,\
    BillingDataUpdateView


urlpatterns = [
    path('accounts/login/', LoginFormView.as_view(), name='login'),
    path('accounts/logout/',logout, name='logout'),
    path('', HistoryListView.as_view(), name='top'),
    path('customer_select/brycen_file_upload/', CustomerSelectAndBrycenFileUpLoadView.as_view(), name='customer_brycen_file_select'),
    path('matched_data/<int:pk>/', SelectFileOrBillingDataFormView.as_view(), name='select_billing_file_or_form'),
    path('matched_data/<int:pk>/billing_data/create/', BillingDataCreateView.as_view(), name='billing_data_create'),
    path('matched_data/<int:matched_data_pk>/billing_data/<int:billing_data_last_row_pk>/', BillingDataDetailView.as_view(), name='billing_data_detail'),
    path('matched_data/<int:matched_data_pk>/billing_data/<int:billing_data_last_row_pk>/edit/', BillingDataUpdateView.as_view(), name='billing_data_edit'),
    path('matched_data/<int:pk>/detail_and_create/',MatchedDataDetailAndVisuallyMatchedDataCreateView.as_view(), name='detail_and_create'),
    path('visually_match/<int:pk>/import_data/', ImportDataCreateView.as_view(), name='import_data'),
    path('import_data/<int:pk>/', ImportDataDetailView.as_view(), name='import_data_detail'),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)