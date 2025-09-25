from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta, datetime
from .models import Ticket, EscalationRule, EscalationLog, EscalationSettings
from apps.notifications.utils import create_notification
from apps.notifications.email_service import EmailService
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task
def process_ticket_escalations():
    """
    Tarea principal que procesa todos los tickets que necesitan escalamiento
    Se ejecuta cada 15 minutos para verificar tickets pendientes
    """
    try:
        now = timezone.now()
        escalated_count = 0
        
        # Obtener tickets que necesitan escalamiento
        tickets_to_escalate = Ticket.objects.filter(
            status__in=['OPEN', 'IN_PROGRESS'],
            escalation_paused=False,
            next_escalation_at__lte=now
        ).select_related('company', 'created_by', 'assigned_to')
        
        logger.info(f"Procesando {tickets_to_escalate.count()} tickets para escalamiento")
        
        for ticket in tickets_to_escalate:
            try:
                if escalate_ticket(ticket.id):
                    escalated_count += 1
            except Exception as e:
                logger.error(f"Error escalando ticket {ticket.reference}: {e}")
        
        logger.info(f"Escalamiento completado: {escalated_count} tickets escalados")
        return f"Escalados {escalated_count} tickets"
        
    except Exception as e:
        logger.error(f"Error en process_ticket_escalations: {e}")
        raise

@shared_task
def escalate_ticket(ticket_id):
    """
    Escala un ticket específico al siguiente nivel
    """
    try:
        ticket = Ticket.objects.select_related('company', 'created_by', 'assigned_to').get(id=ticket_id)
        
        # Verificar si el escalamiento está habilitado
        settings = get_escalation_settings(ticket.company)
        if not settings.enabled:
            logger.info(f"Escalamiento deshabilitado para ticket {ticket.reference}")
            return False
        
        # Verificar horario laboral si está configurado
        if settings.business_hours_only and not settings.is_business_time(timezone.now()):
            # Reprogramar para el próximo horario laboral
            next_business_time = calculate_next_business_time(settings)
            ticket.next_escalation_at = next_business_time
            ticket.save()
            logger.info(f"Ticket {ticket.reference} reprogramado para horario laboral: {next_business_time}")
            return False
        
        # Obtener la regla de escalamiento
        next_level = ticket.escalation_level + 1
        escalation_rule = get_escalation_rule(ticket, next_level)
        
        if not escalation_rule:
            logger.warning(f"No hay regla de escalamiento para ticket {ticket.reference} nivel {next_level}")
            return False
        
        # Verificar nivel máximo
        if next_level > settings.max_escalation_level:
            logger.info(f"Ticket {ticket.reference} alcanzó nivel máximo de escalamiento")
            return False
        
        # Realizar el escalamiento
        previous_assigned = ticket.assigned_to
        ticket.escalation_level = next_level
        
        if settings.auto_assign_on_escalation:
            ticket.assigned_to = escalation_rule.escalate_to
        
        # Calcular próximo escalamiento
        ticket.next_escalation_at = calculate_next_escalation_time(ticket, escalation_rule, settings)
        ticket.save()
        
        # Registrar el escalamiento
        EscalationLog.objects.create(
            ticket=ticket,
            escalation_rule=escalation_rule,
            action='escalated',
            from_user=previous_assigned,
            to_user=escalation_rule.escalate_to,
            level=next_level,
            notes=f"Escalamiento automático después de {escalation_rule.hours_to_escalate} horas sin respuesta"
        )
        
        # Enviar notificaciones
        send_escalation_notifications(ticket, escalation_rule, previous_assigned)
        
        logger.info(f"Ticket {ticket.reference} escalado a nivel {next_level} -> {escalation_rule.escalate_to.username}")
        return True
        
    except Ticket.DoesNotExist:
        logger.error(f"Ticket {ticket_id} no encontrado")
        return False
    except Exception as e:
        logger.error(f"Error escalando ticket {ticket_id}: {e}")
        raise

@shared_task
def update_ticket_escalation_times():
    """
    Actualiza los tiempos de escalamiento para tickets activos
    Se ejecuta cuando se crean nuevos tickets o se responden
    """
    try:
        updated_count = 0
        
        # Tickets activos sin escalamiento programado
        tickets = Ticket.objects.filter(
            status__in=['OPEN', 'IN_PROGRESS'],
            escalation_paused=False,
            next_escalation_at__isnull=True
        ).select_related('company')
        
        for ticket in tickets:
            settings = get_escalation_settings(ticket.company)
            if settings.enabled:
                next_level = ticket.escalation_level + 1
                escalation_rule = get_escalation_rule(ticket, next_level)
                
                if escalation_rule:
                    ticket.next_escalation_at = calculate_next_escalation_time(ticket, escalation_rule, settings)
                    ticket.save()
                    updated_count += 1
        
        logger.info(f"Actualizados tiempos de escalamiento para {updated_count} tickets")
        return f"Actualizados {updated_count} tickets"
        
    except Exception as e:
        logger.error(f"Error actualizando tiempos de escalamiento: {e}")
        raise

@shared_task
def pause_escalation_on_response(ticket_id, message_id):
    """
    Pausa el escalamiento cuando hay una respuesta al ticket
    """
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        settings = get_escalation_settings(ticket.company)
        
        if settings.pause_on_response and not ticket.escalation_paused:
            ticket.escalation_paused = True
            ticket.last_response_at = timezone.now()
            ticket.save()
            
            # Registrar la pausa
            EscalationLog.objects.create(
                ticket=ticket,
                action='paused',
                level=ticket.escalation_level,
                notes="Escalamiento pausado por respuesta al ticket"
            )
            
            logger.info(f"Escalamiento pausado para ticket {ticket.reference}")
            return True
        
        return False
        
    except Ticket.DoesNotExist:
        logger.error(f"Ticket {ticket_id} no encontrado")
        return False
    except Exception as e:
        logger.error(f"Error pausando escalamiento: {e}")
        raise

@shared_task
def resume_escalation(ticket_id):
    """
    Reanuda el escalamiento de un ticket
    """
    try:
        ticket = Ticket.objects.get(id=ticket_id)
        settings = get_escalation_settings(ticket.company)
        
        if ticket.escalation_paused:
            ticket.escalation_paused = False
            
            # Recalcular próximo escalamiento
            next_level = ticket.escalation_level + 1
            escalation_rule = get_escalation_rule(ticket, next_level)
            
            if escalation_rule:
                ticket.next_escalation_at = calculate_next_escalation_time(ticket, escalation_rule, settings)
            
            ticket.save()
            
            # Registrar la reanudación
            EscalationLog.objects.create(
                ticket=ticket,
                action='resumed',
                level=ticket.escalation_level,
                notes="Escalamiento reanudado manualmente"
            )
            
            logger.info(f"Escalamiento reanudado para ticket {ticket.reference}")
            return True
        
        return False
        
    except Ticket.DoesNotExist:
        logger.error(f"Ticket {ticket_id} no encontrado")
        return False
    except Exception as e:
        logger.error(f"Error reanudando escalamiento: {e}")
        raise

def get_escalation_settings(company):
    """Obtiene la configuración de escalamiento para una empresa"""
    try:
        if company:
            return EscalationSettings.objects.get(company=company)
    except EscalationSettings.DoesNotExist:
        pass
    
    # Configuración global por defecto
    try:
        return EscalationSettings.objects.get(company__isnull=True)
    except EscalationSettings.DoesNotExist:
        # Crear configuración por defecto
        return EscalationSettings.objects.create(
            company=None,
            enabled=True,
            business_hours_only=True,
            max_escalation_level=3
        )

def get_escalation_rule(ticket, level):
    """Obtiene la regla de escalamiento para un ticket y nivel específico"""
    try:
        # Buscar regla específica de la empresa
        if ticket.company:
            return EscalationRule.objects.get(
                company=ticket.company,
                priority=ticket.priority,
                level=level,
                is_active=True
            )
    except EscalationRule.DoesNotExist:
        pass
    
    # Buscar regla global
    try:
        return EscalationRule.objects.get(
            company__isnull=True,
            priority=ticket.priority,
            level=level,
            is_active=True
        )
    except EscalationRule.DoesNotExist:
        return None

def calculate_next_escalation_time(ticket, escalation_rule, settings):
    """Calcula el próximo tiempo de escalamiento"""
    base_time = ticket.last_response_at or ticket.created_at
    escalation_time = base_time + timedelta(hours=escalation_rule.hours_to_escalate)
    
    if settings.business_hours_only:
        escalation_time = adjust_to_business_hours(escalation_time, settings)
    
    return escalation_time

def adjust_to_business_hours(target_time, settings):
    """Ajusta un tiempo al próximo horario laboral"""
    business_days = settings.get_business_days_list()
    
    while True:
        weekday = target_time.isoweekday()
        hour = target_time.hour
        
        # Si es día laboral y hora laboral, retornar
        if weekday in business_days and settings.business_start_hour <= hour < settings.business_end_hour:
            return target_time
        
        # Si es día laboral pero fuera de horario, mover al inicio del horario
        if weekday in business_days and hour < settings.business_start_hour:
            return target_time.replace(hour=settings.business_start_hour, minute=0, second=0, microsecond=0)
        
        # Mover al siguiente día laboral
        target_time = target_time.replace(hour=settings.business_start_hour, minute=0, second=0, microsecond=0)
        target_time += timedelta(days=1)

def calculate_next_business_time(settings):
    """Calcula el próximo horario laboral"""
    now = timezone.now()
    return adjust_to_business_hours(now, settings)

def send_escalation_notifications(ticket, escalation_rule, previous_assigned):
    """Envía notificaciones de escalamiento"""
    # Notificar al nuevo asignado
    if escalation_rule.escalate_to:
        message = escalation_rule.notification_template or f"Ticket escalado a nivel {ticket.escalation_level}: {ticket.title}"
        
        create_notification(
            recipient=escalation_rule.escalate_to,
            notification_type='ticket_escalated',
            verb=f"Ticket escalado: {ticket.title}",
            description=message,
            object_id=ticket.id
        )
    
    # Notificar al creador del ticket
    if ticket.created_by:
        create_notification(
            recipient=ticket.created_by,
            notification_type='ticket_escalated',
            verb=f"Tu ticket ha sido escalado: {ticket.title}",
            description=f"El ticket ha sido escalado a nivel {ticket.escalation_level}",
            object_id=ticket.id
        )
    
    # Enviar emails si está habilitado
    settings = get_escalation_settings(ticket.company)
    if settings.email_notifications:
        # Aquí puedes agregar el envío de emails específicos para escalamiento
        pass

@shared_task
def generate_escalation_report():
    """
    Genera reporte diario de escalamientos
    """
    try:
        yesterday = timezone.now() - timedelta(days=1)
        
        escalations = EscalationLog.objects.filter(
            created_at__gte=yesterday,
            action='escalated'
        ).select_related('ticket', 'escalation_rule', 'to_user')
        
        report_data = {
            'total_escalations': escalations.count(),
            'by_level': {},
            'by_priority': {},
            'by_company': {}
        }
        
        for escalation in escalations:
            # Por nivel
            level = escalation.level
            report_data['by_level'][level] = report_data['by_level'].get(level, 0) + 1
            
            # Por prioridad
            priority = escalation.ticket.priority
            report_data['by_priority'][priority] = report_data['by_priority'].get(priority, 0) + 1
            
            # Por empresa
            company = escalation.ticket.company.name if escalation.ticket.company else 'Sin empresa'
            report_data['by_company'][company] = report_data['by_company'].get(company, 0) + 1
        
        logger.info(f"Reporte de escalamiento generado: {report_data}")
        return report_data
        
    except Exception as e:
        logger.error(f"Error generando reporte de escalamiento: {e}")
        raise
