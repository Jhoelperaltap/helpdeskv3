from django.urls import path
from .views import DashboardView
from .views import DashboardDataView, ExportReportView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('api/data/', DashboardDataView.as_view(), name='dashboard_data'),
    path('export/', ExportReportView.as_view(), name='export_report'),
]
