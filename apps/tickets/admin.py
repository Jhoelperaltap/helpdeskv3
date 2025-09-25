from django.contrib import admin
from .models import Ticket, TicketMessage, TicketAttachment, SavedFilter, EscalationRule, EscalationLog, EscalationSettings


@admin.register(EscalationRule)
class EscalationRuleAdmin(admin.ModelAdmin):
    list_display = ['company', 'priority', 'level', 'hours_to_escalate', 'escalate_to', 'is_active']
    list_filter = ['company', 'priority', 'level', 'is_active']
    search_fields = ['company__name', 'escalate_to__username', 'escalate_to__first_name', 'escalate_to__last_name']
    ordering = ['company', 'priority', 'level']
    
    fieldsets = (
        ('Configuración Básica', {
            'fields': ('company', 'priority', 'level', 'hours_to_escalate', 'escalate_to')
        }),
        ('Configuración Avanzada', {
            'fields': ('notification_template', 'is_active'),
            'classes': ('collapse',)
        }),
    )

@admin.register(EscalationLog)
class EscalationLogAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'action', 'level', 'from_user', 'to_user', 'created_at']
    list_filter = ['action', 'level', 'created_at']
    search_fields = ['ticket__reference', 'ticket__title', 'from_user__username', 'to_user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

@admin.register(EscalationSettings)
class EscalationSettingsAdmin(admin.ModelAdmin):
    list_display = ['company', 'enabled', 'business_hours_only', 'max_escalation_level']
    list_filter = ['enabled', 'business_hours_only']
    
    fieldsets = (
        ('Configuración General', {
            'fields': ('company', 'enabled', 'max_escalation_level')
        }),
        ('Horario Laboral', {
            'fields': ('business_hours_only', 'business_start_hour', 'business_end_hour', 'business_days')
        }),
        ('Comportamiento', {
            'fields': ('auto_assign_on_escalation', 'pause_on_response', 'email_notifications')
        }),
    )
