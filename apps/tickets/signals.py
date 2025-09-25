from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail, get_connection, EmailMessage
from django.conf import settings
from django.utils import timezone
from .models import Ticket, TicketMessage, EscalationSettings
from .tasks import update_ticket_escalation_times, pause_escalation_on_response
import logging
import os

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Ticket)
def ticket_created(sender, instance, created, **kwargs):
    """
    Signal handler for when a ticket is created.
    Sends email notification using SMTP configuration from .env
    """
    if created:
        try:
            smtp_connection = get_connection(
                backend='django.core.mail.backends.smtp.EmailBackend',
                host=os.environ.get('EMAIL_HOST', settings.EMAIL_HOST),
                port=int(os.environ.get('EMAIL_PORT', settings.EMAIL_PORT)),
                username=os.environ.get('EMAIL_HOST_USER', settings.EMAIL_HOST_USER),
                password=os.environ.get('EMAIL_HOST_PASSWORD', settings.EMAIL_HOST_PASSWORD),
                use_tls=os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true',
            )
            
            # Verificar que tenemos configuración SMTP
            if not smtp_connection.username or not smtp_connection.password:
                logger.warning(f'Configuración SMTP incompleta para notificación de ticket {instance.reference}')
                return
            
            # Crear email HTML profesional
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>🎫 Nuevo Ticket Creado</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 20px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                    .header {{ background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; padding: 30px 20px; text-align: center; }}
                    .content {{ padding: 30px; }}
                    .ticket-box {{ background: #f0f9ff; border: 1px solid #bae6fd; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 20px; margin: 20px 0; }}
                    .priority-high {{ color: #dc2626; font-weight: bold; }}
                    .priority-medium {{ color: #d97706; font-weight: bold; }}
                    .priority-low {{ color: #059669; font-weight: bold; }}
                    .footer {{ background: #1f2937; color: #9ca3af; padding: 20px; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎫 Nuevo Ticket Creado</h1>
                        <p>Sistema de Helpdesk - Notificación Automática</p>
                    </div>
                    <div class="content">
                        <p>Se ha creado un nuevo ticket en el sistema:</p>
                        
                        <div class="ticket-box">
                            <h3 style="margin-top: 0; color: #374151;">#{instance.reference} - {instance.title}</h3>
                            <p><strong>Prioridad:</strong> <span class="priority-{instance.priority.lower()}">{instance.get_priority_display()}</span></p>
                            <p><strong>Empresa:</strong> {instance.company.name}</p>
                            <p><strong>Creado por:</strong> {instance.created_by.get_full_name() or instance.created_by.username}</p>
                            <p><strong>Email:</strong> {instance.created_by.email or 'No especificado'}</p>
                            <p><strong>Fecha:</strong> {instance.created_at.strftime('%d/%m/%Y %H:%M')}</p>
                            
                            <div style="background: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
                                <p style="margin: 0;"><strong>Descripción:</strong></p>
                                <p style="margin: 5px 0 0 0; color: #6b7280;">{instance.description}</p>
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
            admin_email = getattr(settings, 'ADMIN_EMAIL', None) or os.environ.get('ADMIN_EMAIL')
            if admin_email:
                email = EmailMessage(
                    subject=f'[Helpdesk] 🎫 Nuevo Ticket #{instance.reference} - {instance.title}',
                    body=html_content,
                    from_email=os.environ.get('DEFAULT_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
                    to=[admin_email],
                    connection=smtp_connection,
                )
                email.content_subtype = 'html'
                email.send()
                
                logger.info(f'Notificación HTML enviada para ticket {instance.reference} a {admin_email}')
            else:
                logger.warning(f'No se encontró ADMIN_EMAIL para notificación de ticket {instance.reference}')
            
        except Exception as e:
            logger.error(f'Error enviando notificación para ticket {instance.reference}: {str(e)}')

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
