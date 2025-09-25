from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from .models import Notification
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/list.html'
    context_object_name = 'object_list'
    login_url = '/users/login/'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = self.get_queryset().filter(is_read=False).count()
        return context

@method_decorator(login_required, name='dispatch')
class MarkAsReadView(View):
    def post(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.mark_as_read()
        
        channel_layer = get_channel_layer()
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        
        async_to_sync(channel_layer.group_send)(
            f"notifications_{request.user.id}",
            {
                'type': 'notification_message',
                'message_type': 'unread_count',
                'count': unread_count
            }
        )
        
        return JsonResponse({'status': 'success', 'unread_count': unread_count})

@method_decorator(login_required, name='dispatch')
class MarkAllAsReadView(View):
    def post(self, request):
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False)
        count = unread_notifications.count()
        
        for notification in unread_notifications:
            notification.mark_as_read()
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"notifications_{request.user.id}",
            {
                'type': 'notification_message',
                'message_type': 'unread_count',
                'count': 0
            }
        )
        
        return JsonResponse({'status': 'success', 'count': count, 'unread_count': 0})
