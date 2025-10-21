from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail, get_connection, EmailMessage
from django.conf import settings
from django.utils import timezone
from .models import Ticket, TicketMessage, EscalationSettings, EmailLog
from .tasks import update_ticket_escalation_times, pause_escalation_on_response
import logging
import os
import threading
import smtplib

logger = logging.getLogger(__name__)

def send_ticket_notification_async(ticket_id, ticket_reference, ticket_title, ticket_priority, 
                                   ticket_description, company_name, created_by_name, 
                                   created_by_email, created_at):
    """
    Envía notificación de ticket de forma asíncrona para evitar timeouts
    """
    try:
        # Configuración SMTP desde .env
        smtp_host = os.environ.get('EMAIL_HOST', settings.EMAIL_HOST)
        smtp_port = int(os.environ.get('EMAIL_PORT', settings.EMAIL_PORT))
        smtp_user = os.environ.get('EMAIL_HOST_USER', settings.EMAIL_HOST_USER)
        smtp_password = os.environ.get('EMAIL_HOST_PASSWORD', settings.EMAIL_HOST_PASSWORD)
        from_email = os.environ.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)
        admin_email = os.environ.get('ADMIN_EMAIL', settings.ADMIN_EMAIL)
        
        # Verificar configuración
        if not smtp_user or not smtp_password or not admin_email:
            raise ValueError('Configuración SMTP incompleta')
        
        # Determinar si usar SSL o TLS basado en el puerto
        use_ssl = smtp_port == 465
        use_tls = smtp_port == 587
        
        # Crear log de email
        email_log = EmailLog.objects.create(
            email_type='ticket_notification',
            recipient=admin_email,
            subject=f'[Helpdesk] Nuevo Ticket #{ticket_reference} - {ticket_title}',
            status='sending',
            smtp_host=smtp_host,
            smtp_port=smtp_port
        )
        
        # Crear email HTML profesional
        priority_map = {
            'LOW': 'Baja',
            'MEDIUM': 'Media',
            'HIGH': 'Alta',
            'URGENT': 'Urgente'
        }
        priority_display = priority_map.get(ticket_priority, ticket_priority)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Nuevo Ticket Creado</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 30px 20px; text-align: center; }}
                .content {{ padding: 30px; }}
                .ticket-box {{ background: #f0f9ff; border: 1px solid #bae6fd; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                .priority-high {{ color: #dc2626; font-weight: bold; }}
                .priority-medium {{ color: #d97706; font-weight: bold; }}
                .priority-low {{ color: #059669; font-weight: bold; }}
                .priority-urgent {{ color: #991b1b; font-weight: bold; }}
                .footer {{ background: #1f2937; color: #9ca3af; padding: 20px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Nuevo Ticket Creado</h1>
                    <p>Sistema de Helpdesk - Notificación Automática</p>
                </div>
                <div class="content">
                    <p>Se ha creado un nuevo ticket en el sistema:</p>
                    
                    <div class="ticket-box">
                        <h3 style="margin-top: 0; color: #374151;">#{ticket_reference} - {ticket_title}</h3>
                        <p><strong>Prioridad:</strong> <span class="priority-{ticket_priority.lower()}">{priority_display}</span></p>
                        <p><strong>Empresa:</strong> {company_name}</p>
                        <p><strong>Creado por:</strong> {created_by_name}</p>
                        <p><strong>Email:</strong> {created_by_email or 'No especificado'}</p>
                        <p><strong>Fecha:</strong> {created_at}</p>
                        
                        <div style="background: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
                            <p style="margin: 0;"><strong>Descripción:</strong></p>
                            <p style="margin: 5px 0 0 0; color: #6b7280;">{ticket_description}</p>
                        </div>
                    </div>
                    
                    <p>Puedes ver y gestionar este ticket accediendo al sistema de helpdesk.</p>
                </div>
                <div class="footer">
                    <p><strong>Sistema Helpdesk</strong></p>
                    <p style="font-size: 12px;">Este es un email automático, no responder.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Enviar email HTML
        email = EmailMessage(
            subject=f'[Helpdesk] Nuevo Ticket #{ticket_reference} - {ticket_title}',
            body=html_content,
            from_email=from_email,
            to=[admin_email],
            connection=get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=smtp_host,
                port=smtp_port,
                username=smtp_user,
                password=smtp_password,
                use_ssl=use_ssl,
                use_tls=use_tls,
                timeout=60,  # Timeout de 60 segundos para producción
            ),
        )
        email.content_subtype = 'html'
        email.send()
        
        # Actualizar log como exitoso
        email_log.status = 'sent'
        email_log.sent_at = timezone.now()
        email_log.save()
        
        logger.info(f'Notificación enviada para ticket {ticket_reference} a {admin_email}')
        
    except smtplib.SMTPException as e:
        error_msg = f'Error SMTP: {str(e)}'
        email_log.status = 'failed'
        email_log.error_message = error_msg
        email_log.save()
        logger.error(f'Error SMTP enviando notificación para ticket {ticket_reference}: {error_msg}')
        
    except Exception as e:
        error_msg = str(e)
        email_log.status = 'failed'
        email_log.error_message = error_msg
        email_log.save()
        logger.error(f'Error enviando notificación para ticket {ticket_reference}: {error_msg}')
        
    except Exception as e:
        logger.error(f'Error crítico en envío asíncrono de notificación: {str(e)}')

@receiver(post_save, sender=Ticket)
def ticket_created(sender, instance, created, **kwargs):
    """
    Signal handler for when a ticket is created.
    Sends email notification asynchronously to avoid timeouts
    """
    if created:
        try:
            thread = threading.Thread(
                target=send_ticket_notification_async,
                args=(
                    instance.id,
                    instance.reference,
                    instance.title,
                    instance.priority,
                    instance.description,
                    instance.company.name,
                    instance.created_by.get_full_name() or instance.created_by.username,
                    instance.created_by.email,
                    instance.created_at.strftime('%d/%m/%Y %H:%M'),
                ),
                daemon=True
            )
            thread.start()
            
            logger.info(f'Notificación programada para ticket {instance.reference}')
            
        except Exception as e:
            logger.error(f'Error programando notificación para ticket {instance.reference}: {str(e)}')

@receiver(post_save, sender=Ticket)
def handle_ticket_escalation_on_create(sender, instance, created, **kwargs):
    """
    Configura el escalamiento automático cuando se crea un nuevo ticket
    """
    if created:
        try:
            # Inicializar campos de escalamiento
            instance.escalation_level = 0
            instance.escalation_paused = False
            instance.last_response_at = instance.created_at
            
            # Programar el primer escalamiento si está habilitado
            settings_obj = get_escalation_settings(instance.company)
            if settings_obj and settings_obj.enabled:
                # Ejecutar tarea asíncrona para calcular próximo escalamiento
                update_ticket_escalation_times.delay()
            
            logger.info(f'Escalamiento configurado para ticket {instance.reference}')
            
        except Exception as e:
            logger.error(f'Error configurando escalamiento para ticket {instance.reference}: {str(e)}')

@receiver(pre_save, sender=Ticket)
def handle_ticket_status_change(sender, instance, **kwargs):
    """
    Maneja cambios de estado del ticket para pausar/reanudar escalamiento
    """
    if instance.pk:  # Solo para tickets existentes
        try:
            old_ticket = Ticket.objects.get(pk=instance.pk)
            
            # Si el ticket se resuelve o cierra, pausar escalamiento
            if instance.status in ['RESOLVED', 'CLOSED'] and old_ticket.status not in ['RESOLVED', 'CLOSED']:
                instance.escalation_paused = True
                instance.next_escalation_at = None
                logger.info(f'Escalamiento pausado para ticket {instance.reference} - Estado: {instance.status}')
            
            # Si el ticket se reabre, reanudar escalamiento
            elif instance.status in ['OPEN', 'IN_PROGRESS'] and old_ticket.status in ['RESOLVED', 'CLOSED']:
                instance.escalation_paused = False
                instance.last_response_at = timezone.now()
                # La tarea programada recalculará el próximo escalamiento
                logger.info(f'Escalamiento reanudado para ticket {instance.reference}')
            
            # Si se asigna a alguien nuevo, reiniciar el tiempo de escalamiento
            if instance.assigned_to != old_ticket.assigned_to and instance.assigned_to:
                instance.last_response_at = timezone.now()
                instance.escalation_paused = False
                logger.info(f'Escalamiento reiniciado para ticket {instance.reference} - Nuevo asignado: {instance.assigned_to.username}')
                
        except Ticket.DoesNotExist:
            pass
        except Exception as e:
            logger.error(f'Error manejando cambio de estado para ticket {instance.reference}: {str(e)}')

@receiver(post_save, sender=TicketMessage)
def handle_message_added_escalation(sender, instance, created, **kwargs):
    """
    Pausa el escalamiento cuando se agrega un mensaje al ticket
    """
    if created:
        try:
            ticket = instance.ticket
            settings_obj = get_escalation_settings(ticket.company)
            
            # Solo pausar si la configuración lo permite y el mensaje no es privado
            if settings_obj and settings_obj.pause_on_response and not instance.private:
                # Ejecutar tarea asíncrona para pausar escalamiento
                pause_escalation_on_response.delay(ticket.id, instance.id)
                logger.info(f'Escalamiento pausado por respuesta en ticket {ticket.reference}')
                
        except Exception as e:
            logger.error(f'Error pausando escalamiento por mensaje: {str(e)}')

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
        return None
