from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'verb', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'verb', 'description']
    readonly_fields = ['created_at', 'read_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'sender')
