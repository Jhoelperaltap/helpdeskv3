from django.db import models
from django.conf import settings  # Added settings import
from django.contrib.auth.models import User
from django.utils import timezone

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('ticket_created', 'Ticket Creado'),
        ('ticket_assigned', 'Ticket Asignado'),
        ('ticket_updated', 'Ticket Actualizado'),
        ('ticket_closed', 'Ticket Cerrado'),
        ('ticket_reopened', 'Ticket Reabierto'),
        ('comment_added', 'Comentario Agregado'),
        ('ticket_escalated', 'Ticket Escalado'),  # Agregado tipo de notificación para escalamiento
        ('system', 'Sistema'),
    ]
    
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    verb = models.CharField(max_length=255)  # Mensaje de la notificación
    description = models.TextField(blank=True, null=True)
    
    # Referencia genérica al objeto relacionado (ticket, comentario, etc.)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"{self.recipient.username} - {self.verb}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
