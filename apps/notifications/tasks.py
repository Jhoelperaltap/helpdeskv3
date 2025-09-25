from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from .models import Notification
from .email_service import EmailService
from apps.tickets.models import Ticket, EscalationRule, EscalationLog
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task
def send_email_notification_async(notification_type, **kwargs):
    """
    Asynchronous task to send email notifications
    This allows email sending to happen in the background
    """
    try:
        if notification_type == 'ticket_created':
            ticket_id = kwargs.get('ticket_id')
            ticket = Ticket.objects.get(id=ticket_id)
            EmailService.send_ticket_created_email(ticket)
            
        elif notification_type == 'ticket_updated':
            ticket_id = kwargs.get('ticket_id')
            updated_by_id = kwargs.get('updated_by_id')
            ticket = Ticket.objects.get(id=ticket_id)
            updated_by = User.objects.get(id=updated_by_id)
            EmailService.send_ticket_updated_email(ticket, updated_by)
            
        elif notification_type == 'ticket_resolved':
            ticket_id = kwargs.get('ticket_id')
            ticket = Ticket.objects.get(id=ticket_id)
            EmailService.send_ticket_resolved_email(ticket)
            
        elif notification_type == 'message_added':
            ticket_id = kwargs.get('ticket_id')
            message_id = kwargs.get('message_id')
            sender_id = kwargs.get('sender_id')
            ticket = Ticket.objects.get(id=ticket_id)
            message = ticket.messages.get(id=message_id)
            sender = User.objects.get(id=sender_id)
            EmailService.send_message_added_email(ticket, message, sender)
            
        elif notification_type == 'welcome':
            user_id = kwargs.get('user_id')
            password = kwargs.get('password')
            user = User.objects.get(id=user_id)
            EmailService.send_welcome_email(user, password)
            
        elif notification_type == 'escalation_warning':
            ticket_id = kwargs.get('ticket_id')
            escalation_rule_id = kwargs.get('escalation_rule_id')
            time_remaining = kwargs.get('time_remaining')
            ticket = Ticket.objects.get(id=ticket_id)
            escalation_rule = EscalationRule.objects.get(id=escalation_rule_id)
            EmailService.send_escalation_warning_email(ticket, escalation_rule, time_remaining)
            
        elif notification_type == 'ticket_escalated':
            ticket_id = kwargs.get('ticket_id')
            escalation_rule_id = kwargs.get('escalation_rule_id')
            previous_assigned_id = kwargs.get('previous_assigned_id')
            ticket = Ticket.objects.get(id=ticket_id)
            escalation_rule = EscalationRule.objects.get(id=escalation_rule_id)
            previous_assigned = User.objects.get(id=previous_assigned_id) if previous_assigned_id else None
            EmailService.send_escalation_notification_email(ticket, escalation_rule, previous_assigned)
            
        elif notification_type == 'sla_breach':
            ticket_id = kwargs.get('ticket_id')
            sla_info = kwargs.get('sla_info')
            ticket = Ticket.objects.get(id=ticket_id)
            EmailService.send_sla_breach_notification(ticket, sla_info)
            
        logger.info(f"Email notification sent successfully: {notification_type}")
        
    except Exception as e:
        logger.error(f"Error sending email notification {notification_type}: {e}")
        raise

@shared_task
def cleanup_old_notifications():
    """
    Clean up old notifications (older than 30 days)
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = Notification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        return f"Cleaned up {deleted_count} old notifications"
        
    except Exception as e:
        logger.error(f"Error cleaning up notifications: {e}")
        raise

@shared_task
def send_daily_summary():
    """
    Send daily summary emails to administrators
    """
    try:
        # Get statistics for the last 24 hours
        yesterday = timezone.now() - timedelta(days=1)
        
        new_tickets = Ticket.objects.filter(created_at__gte=yesterday).count()
        resolved_tickets = Ticket.objects.filter(
            updated_at__gte=yesterday,
            status='RESOLVED'
        ).count()
        
        # Send summary to superadmins
        superadmins = User.objects.filter(role='SUPERADMIN', is_active=True)
        
        for admin in superadmins:
            # You can create a daily summary email template
            # EmailService.send_daily_summary_email(admin, new_tickets, resolved_tickets)
            pass
            
        logger.info(f"Daily summary sent to {superadmins.count()} administrators")
        return f"Daily summary sent to {superadmins.count()} administrators"
        
    except Exception as e:
        logger.error(f"Error sending daily summary: {e}")
        raise

@shared_task
def send_escalation_warnings():
    """
    Envía advertencias antes de que ocurra el escalamiento
    Se ejecuta cada 30 minutos para verificar tickets próximos a escalar
    """
    try:
        now = timezone.now()
        warning_time = now + timedelta(hours=1)  # Advertir 1 hora antes
        
        # Buscar tickets que escalarán en la próxima hora
        tickets_to_warn = Ticket.objects.filter(
            status__in=['OPEN', 'IN_PROGRESS'],
            escalation_paused=False,
            next_escalation_at__lte=warning_time,
            next_escalation_at__gt=now,
            escalation_warning_sent=False
        ).select_related('company', 'assigned_to')
        
        warned_count = 0
        
        for ticket in tickets_to_warn:
            try:
                # Obtener la regla de escalamiento
                from apps.tickets.tasks import get_escalation_rule
                next_level = ticket.escalation_level + 1
                escalation_rule = get_escalation_rule(ticket, next_level)
                
                if escalation_rule:
                    time_remaining = ticket.next_escalation_at - now
                    
                    # Enviar advertencia por email
                    send_email_notification_async.delay(
                        'escalation_warning',
                        ticket_id=ticket.id,
                        escalation_rule_id=escalation_rule.id,
                        time_remaining=str(time_remaining)
                    )
                    
                    # Marcar como advertencia enviada
                    ticket.escalation_warning_sent = True
                    ticket.save()
                    
                    warned_count += 1
                    
            except Exception as e:
                logger.error(f"Error enviando advertencia para ticket {ticket.reference}: {e}")
        
        logger.info(f"Enviadas {warned_count} advertencias de escalamiento")
        return f"Enviadas {warned_count} advertencias"
        
    except Exception as e:
        logger.error(f"Error enviando advertencias de escalamiento: {e}")
        raise

@shared_task
def send_escalation_summary_reports():
    """
    Envía reportes de resumen de escalamientos a los administradores
    Se ejecuta diariamente
    """
    try:
        yesterday = timezone.now() - timedelta(days=1)
        
        # Obtener datos de escalamiento del día anterior
        escalations = EscalationLog.objects.filter(
            created_at__gte=yesterday,
            action='escalated'
        ).select_related('ticket', 'escalation_rule', 'to_user')
        
        if not escalations.exists():
            logger.info("No hay escalamientos para reportar")
            return "No hay escalamientos para reportar"
        
        # Agrupar datos por empresa
        company_data = {}
        
        for escalation in escalations:
            company = escalation.ticket.company
            company_name = company.name if company else 'Sin empresa'
            
            if company_name not in company_data:
                company_data[company_name] = {
                    'total_escalations': 0,
                    'by_priority': {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0},
                    'by_level': {},
                    'tickets': []
                }
            
            company_data[company_name]['total_escalations'] += 1
            company_data[company_name]['by_priority'][escalation.ticket.priority] += 1
            
            level = escalation.level
            company_data[company_name]['by_level'][level] = company_data[company_name]['by_level'].get(level, 0) + 1
            
            company_data[company_name]['tickets'].append({
                'reference': escalation.ticket.reference,
                'title': escalation.ticket.title,
                'priority': escalation.ticket.priority,
                'level': escalation.level,
                'escalated_to': escalation.to_user.username if escalation.to_user else 'N/A'
            })
        
        # Enviar reporte a superadmins
        superadmins = User.objects.filter(role='SUPERADMIN', is_active=True)
        
        escalation_data = {
            'period': 'Diario',
            'date': yesterday.strftime('%d/%m/%Y'),
            'total_escalations': escalations.count(),
            'companies': company_data
        }
        
        for admin in superadmins:
            EmailService.send_escalation_summary_email(admin, escalation_data)
        
        # Enviar reporte a administradores de empresa
        for company_name, data in company_data.items():
            if company_name != 'Sin empresa':
                company_admins = User.objects.filter(
                    company__name=company_name,
                    role='COMPANY_ADMIN',
                    is_active=True
                )
                
                company_escalation_data = {
                    'period': 'Diario',
                    'date': yesterday.strftime('%d/%m/%Y'),
                    'total_escalations': data['total_escalations'],
                    'company_data': data
                }
                
                for admin in company_admins:
                    EmailService.send_escalation_summary_email(admin, company_escalation_data)
        
        logger.info(f"Reportes de escalamiento enviados para {len(company_data)} empresas")
        return f"Reportes enviados para {len(company_data)} empresas"
        
    except Exception as e:
        logger.error(f"Error enviando reportes de escalamiento: {e}")
        raise

@shared_task
def check_sla_breaches():
    """
    Verifica tickets que han incumplido SLA y envía notificaciones
    """
    try:
        now = timezone.now()
        breached_count = 0
        
        # Buscar tickets que han superado el tiempo de SLA
        # Esto es un ejemplo básico, puedes ajustar según tus reglas de SLA
        sla_hours = {
            'CRITICAL': 2,
            'HIGH': 8,
            'MEDIUM': 24,
            'LOW': 72
        }
        
        for priority, hours in sla_hours.items():
            sla_deadline = now - timedelta(hours=hours)
            
            breached_tickets = Ticket.objects.filter(
                priority=priority,
                status__in=['OPEN', 'IN_PROGRESS'],
                created_at__lt=sla_deadline,
                sla_breach_notified=False
            )
            
            for ticket in breached_tickets:
                sla_info = {
                    'priority': priority,
                    'sla_hours': hours,
                    'breach_time': now - ticket.created_at,
                    'created_at': ticket.created_at
                }
                
                # Enviar notificación de incumplimiento de SLA
                send_email_notification_async.delay(
                    'sla_breach',
                    ticket_id=ticket.id,
                    sla_info=sla_info
                )
                
                # Marcar como notificado
                ticket.sla_breach_notified = True
                ticket.save()
                
                breached_count += 1
        
        logger.info(f"Detectados {breached_count} incumplimientos de SLA")
        return f"Detectados {breached_count} incumplimientos de SLA"
        
    except Exception as e:
        logger.error(f"Error verificando incumplimientos de SLA: {e}")
        raise
