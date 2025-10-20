from django.db import models
from django.conf import settings
from apps.companies.models import Company
import json

class Ticket(models.Model):
    STATUS = [('OPEN','Abierto'),('IN_PROGRESS','En Progreso'),('RESOLVED','Resuelto'),('CLOSED','Cerrado')]
    PRIORITY = [('LOW','Baja'),('MEDIUM','Media'),('HIGH','Alta')]

    reference = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='OPEN')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='MEDIUM')
    company = models.ForeignKey(Company, related_name='tickets', on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='created_tickets', on_delete=models.SET_NULL, null=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='assigned_tickets', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_response_at = models.DateTimeField(null=True, blank=True, help_text="Última vez que se respondió al ticket")
    escalation_level = models.IntegerField(default=0, help_text="Nivel de escalamiento actual (0=sin escalar)")
    next_escalation_at = models.DateTimeField(null=True, blank=True, help_text="Próxima fecha de escalamiento")
    escalation_paused = models.BooleanField(default=False, help_text="Si el escalamiento está pausado")

    def __str__(self):
        return f"{self.reference} - {self.title}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('tickets:ticket_detail', args=[self.pk])

class TicketMessage(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='messages', on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    private = models.BooleanField(default=False)

    class Meta:
        ordering = ('created_at',)

class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, related_name='attachments', on_delete=models.CASCADE)
    message = models.ForeignKey(TicketMessage, related_name='attachments', on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to='ticket_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class SavedFilter(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='saved_filters', on_delete=models.CASCADE)
    name = models.CharField(max_length=100, help_text="Nombre descriptivo del filtro")
    filter_data = models.JSONField(help_text="Datos del filtro en formato JSON")
    is_default = models.BooleanField(default=False, help_text="Si es el filtro por defecto del usuario")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'name']
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def get_filter_params(self):
        """Convierte los datos JSON a parámetros de filtro"""
        try:
            return json.loads(self.filter_data) if isinstance(self.filter_data, str) else self.filter_data
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_filter_params(self, params_dict):
        """Guarda los parámetros de filtro como JSON"""
        # Filtrar parámetros vacíos
        clean_params = {k: v for k, v in params_dict.items() if v not in ['', None, []]}
        self.filter_data = clean_params
    
    def save(self, *args, **kwargs):
        # Si se marca como default, desmarcar otros filtros default del usuario
        if self.is_default:
            SavedFilter.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

class EscalationRule(models.Model):
    """Reglas de escalamiento automático por empresa y prioridad"""
    PRIORITY_CHOICES = [('LOW','Baja'),('MEDIUM','Media'),('HIGH','Alta')]
    
    company = models.ForeignKey(Company, related_name='escalation_rules', on_delete=models.CASCADE, null=True, blank=True, help_text="Empresa específica (null = regla global)")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, help_text="Prioridad del ticket")
    level = models.IntegerField(help_text="Nivel de escalamiento (1, 2, 3, etc.)")
    hours_to_escalate = models.IntegerField(help_text="Horas sin respuesta antes de escalar")
    escalate_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='escalation_targets', on_delete=models.CASCADE, help_text="Usuario al que escalar")
    notification_template = models.TextField(blank=True, help_text="Template personalizado para la notificación")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['company', 'priority', 'level']
        ordering = ['company', 'priority', 'level']
    
    def __str__(self):
        company_name = self.company.name if self.company else "Global"
        return f"{company_name} - {self.get_priority_display()} - Nivel {self.level}"

class EscalationLog(models.Model):
    """Registro de escalamientos realizados"""
    ACTION_CHOICES = [
        ('escalated', 'Escalado'),
        ('assigned', 'Asignado'),
        ('paused', 'Pausado'),
        ('resumed', 'Reanudado'),
        ('resolved', 'Resuelto'),
    ]
    
    ticket = models.ForeignKey(Ticket, related_name='escalation_logs', on_delete=models.CASCADE)
    escalation_rule = models.ForeignKey(EscalationRule, related_name='logs', on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='escalations_from', on_delete=models.SET_NULL, null=True, blank=True)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='escalations_to', on_delete=models.SET_NULL, null=True, blank=True)
    level = models.IntegerField(help_text="Nivel de escalamiento")
    notes = models.TextField(blank=True, help_text="Notas adicionales sobre el escalamiento")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='escalation_actions', on_delete=models.SET_NULL, null=True, blank=True, help_text="Usuario que realizó la acción")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.ticket.reference} - {self.get_action_display()} - Nivel {self.level}"

class EscalationSettings(models.Model):
    """Configuración global del sistema de escalamiento"""
    company = models.OneToOneField(Company, related_name='escalation_settings', on_delete=models.CASCADE, null=True, blank=True, help_text="Empresa específica (null = configuración global)")
    enabled = models.BooleanField(default=True, help_text="Si el escalamiento automático está habilitado")
    business_hours_only = models.BooleanField(default=True, help_text="Solo escalar en horario laboral")
    business_start_hour = models.IntegerField(default=9, help_text="Hora de inicio del horario laboral (0-23)")
    business_end_hour = models.IntegerField(default=17, help_text="Hora de fin del horario laboral (0-23)")
    business_days = models.CharField(max_length=20, default="1,2,3,4,5", help_text="Días laborales (1=Lunes, 7=Domingo)")
    max_escalation_level = models.IntegerField(default=3, help_text="Nivel máximo de escalamiento")
    auto_assign_on_escalation = models.BooleanField(default=True, help_text="Asignar automáticamente al escalar")
    pause_on_response = models.BooleanField(default=True, help_text="Pausar escalamiento cuando hay respuesta")
    email_notifications = models.BooleanField(default=True, help_text="Enviar notificaciones por email")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Escalamiento"
        verbose_name_plural = "Configuraciones de Escalamiento"
    
    def __str__(self):
        company_name = self.company.name if self.company else "Global"
        return f"Configuración de {company_name}"
    
    def get_business_days_list(self):
        """Retorna lista de días laborales como enteros"""
        return [int(day) for day in self.business_days.split(',') if day.strip()]
    
    def is_business_time(self, datetime_obj):
        """Verifica si una fecha/hora está en horario laboral"""
        if not self.business_hours_only:
            return True
        
        weekday = datetime_obj.isoweekday()  # 1=Monday, 7=Sunday
        if weekday not in self.get_business_days_list():
            return False
        
        hour = datetime_obj.hour
        return self.business_start_hour <= hour < self.business_end_hour

class EmailLog(models.Model):
    """Registro de intentos de envío de email para debugging"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('sending', 'Enviando'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
    ]
    
    TYPE_CHOICES = [
        ('basic', 'Email Básico'),
        ('html', 'Email HTML'),
        ('ticket_notification', 'Notificación de Ticket'),
        ('bulk', 'Envío Masivo'),
        ('connection_test', 'Prueba de Conexión'),
    ]
    
    email_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    recipient = models.EmailField()
    subject = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    smtp_host = models.CharField(max_length=255, blank=True)
    smtp_port = models.IntegerField(null=True, blank=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_email_type_display()} a {self.recipient} - {self.get_status_display()}"
