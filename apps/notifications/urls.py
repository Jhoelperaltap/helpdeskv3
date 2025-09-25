from django.urls import path
from .views import NotificationListView, MarkAsReadView, MarkAllAsReadView

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification_list'),
    path('mark-read/<int:notification_id>/', MarkAsReadView.as_view(), name='mark_as_read'),
    path('mark-all-read/', MarkAllAsReadView.as_view(), name='mark_all_as_read'),
]
