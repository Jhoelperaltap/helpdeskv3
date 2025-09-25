from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
from apps.tickets.models import Ticket
from apps.notifications.models import Notification
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class EmailService:
    """Service for sending email notifications"""
    
    @staticmethod
    def send_ticket_created_email(ticket):
        """Send email when a new ticket is created"""
        if not settings.EMAIL_NOTIFICATIONS_ENABLED:
            return
            
        try:
            # Send to assigned technician if exists
            if ticket.assigned_to:
                EmailService._send_email_to_user(
                    user=ticket.assigned_to,
                    template_name='emails/ticket_created',
                    subject=f'Nuevo ticket asignado: {ticket.title}',
                    context={'ticket': ticket, 'user': ticket.assigned_to}
                )
            
            # Send to company admins
            company_admins = User.objects.filter(
                company=ticket.company,
                role__in=['COMPANY_ADMIN', 'SUPERADMIN']
            )
            
            for admin in company_admins:
                EmailService._send_email_to_user(
                    user=admin,
                    template_name='emails/ticket_created',
                    subject=f'Nuevo ticket creado: {ticket.title}',
                    context={'ticket': ticket, 'user': admin}
                )
                
        except Exception as e:
            logger.error(f"Error sending ticket created email: {e}")
    
    @staticmethod
    def send_ticket_updated_email(ticket, updated_by):
        """Send email when a ticket is updated"""
        if not settings.EMAIL_NOTIFICATIONS_ENABLED:
            return
            
        try:
            # Send to ticket creator
            if ticket.created_by != updated_by:
                EmailService._send_email_to_user(
                    user=ticket.created_by,
                    template_name='emails/ticket_updated',
                    subject=f'Ticket actualizado: {ticket.title}',
                    context={'ticket': ticket, 'user': ticket.created_by, 'updated_by': updated_by}
                )
            
            # Send to assigned technician if different from updater
            if ticket.assigned_to and ticket.assigned_to != updated_by:
                EmailService._send_email_to_user(
                    user=ticket.assigned_to,
                    template_name='emails/ticket_updated',
                    subject=f'Ticket actualizado: {ticket.title}',
                    context={'ticket': ticket, 'user': ticket.assigned_to, 'updated_by': updated_by}
                )
                
        except Exception as e:
            logger.error(f"Error sending ticket updated email: {e}")
    
    @staticmethod
    def send_ticket_resolved_email(ticket):
        """Send email when a ticket is resolved"""
        if not settings.EMAIL_NOTIFICATIONS_ENABLED:
            return
            
        try:
            EmailService._send_email_to_user(
                user=ticket.created_by,
                template_name='emails/ticket_resolved',
                subject=f'Ticket resuelto: {ticket.title}',
                context={'ticket': ticket, 'user': ticket.created_by}
            )
        except Exception as e:
            logger.error(f"Error sending ticket resolved email: {e}")
    
    @staticmethod
    def send_message_added_email(ticket, message, sender):
        """Send email when a new message is added to a ticket"""
        if not settings.EMAIL_NOTIFICATIONS_ENABLED:
            return
            
        try:
            # Send to all participants except the sender
            participants = set()
            participants.add(ticket.created_by)
            if ticket.assigned_to:
                participants.add(ticket.assigned_to)
            
            # Remove sender from participants
            participants.discard(sender)
            
            for participant in participants:
                EmailService._send_email_to_user(
                    user=participant,
                    template_name='emails/message_added',
                    subject=f'Nuevo mensaje en ticket: {ticket.title}',
                    context={
                        'ticket': ticket, 
                        'message': message, 
                        'sender': sender,
                        'user': participant
                    }
                )
                
        except Exception as e:
            logger.error(f"Error sending message added email: {e}")
    
    @staticmethod
    def send_welcome_email(user, password=None):
        """Send welcome email to new users"""
        if not settings.EMAIL_NOTIFICATIONS_ENABLED:
            return
            
        try:
            EmailService._send_email_to_user(
                user=user,
                template_name='emails/welcome',
                subject='Bienvenido al Sistema de Helpdesk',
                context={'user': user, 'password': password}
            )
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
    
    @staticmethod
    def send_escalation_warning_email(ticket, escalation_rule, time_remaining):
        """Send warning email before escalation occurs"""
        if not settings.EMAIL_NOTIFICATIONS_ENABLED:
            return
            
        try:
            # Send to current assigned user
            if ticket.assigned_to:
                EmailService._send_email_to_user(
                    user=ticket.assigned_to,
                    template_name='emails/escalation_warning',
                    subject=f'⚠️ Ticket será escalado pronto: {ticket.title}',
                    context={
                        'ticket': ticket,
                        'escalation_rule': escalation_rule,
                        'time_remaining': time_remaining,
                        'user': ticket.assigned_to
                    }
                )
            
            # Send to company admins if no one is assigned
            if not ticket.assigned_to:
                company_admins = User.objects.filter(
                    company=ticket.company,
                    role__in=['COMPANY_ADMIN', 'SUPERADMIN']
                )
                
                for admin in company_admins:
                    EmailService._send_email_to_user(
                        user=admin,
                        template_name='emails/escalation_warning',
                        subject=f'⚠️ Ticket será escalado pronto: {ticket.title}',
                        context={
                            'ticket': ticket,
                            'escalation_rule': escalation_rule,
                            'time_remaining': time_remaining,
                            'user': admin
                        }
                    )
                    
        except Exception as e:
            logger.error(f"Error sending escalation warning email: {e}")
    
    @staticmethod
    def send_escalation_notification_email(ticket, escalation_rule, previous_assigned):
        """Send email when ticket is escalated"""
        if not settings.EMAIL_NOTIFICATIONS_ENABLED:
            return
            
        try:
            # Send to new assigned user
            if escalation_rule.escalate_to:
                EmailService._send_email_to_user(
                    user=escalation_rule.escalate_to,
                    template_name='emails/ticket_escalated',
                    subject=f'🔺 Ticket escalado a ti: {ticket.title}',
                    context={
                        'ticket': ticket,
                        'escalation_rule': escalation_rule,
                        'previous_assigned': previous_assigned,
                        'user': escalation_rule.escalate_to
                    }
                )
            
            # Send to ticket creator
            if ticket.created_by:
                EmailService._send_email_to_user(
                    user=ticket.created_by,
                    template_name='emails/escalation_customer_notification',
                    subject=f'Tu ticket ha sido escalado: {ticket.title}',
                    context={
                        'ticket': ticket,
                        'escalation_rule': escalation_rule,
                        'user': ticket.created_by
                    }
                )
            
            # Send to previous assigned user if exists
            if previous_assigned and previous_assigned != escalation_rule.escalate_to:
                EmailService._send_email_to_user(
                    user=previous_assigned,
                    template_name='emails/escalation_previous_assigned',
                    subject=f'Ticket escalado desde tu asignación: {ticket.title}',
                    context={
                        'ticket': ticket,
                        'escalation_rule': escalation_rule,
                        'new_assigned': escalation_rule.escalate_to,
                        'user': previous_assigned
                    }
                )
                
        except Exception as e:
            logger.error(f"Error sending escalation notification email: {e}")
    
    @staticmethod
    def send_escalation_summary_email(user, escalation_data):
        """Send daily/weekly escalation summary to managers"""
        if not settings.EMAIL_NOTIFICATIONS_ENABLED:
            return
            
        try:
            EmailService._send_email_to_user(
                user=user,
                template_name='emails/escalation_summary',
                subject=f'📊 Resumen de Escalamientos - {escalation_data.get("period", "Diario")}',
                context={
                    'escalation_data': escalation_data,
                    'user': user
                }
            )
        except Exception as e:
            logger.error(f"Error sending escalation summary email: {e}")
    
    @staticmethod
    def send_sla_breach_notification(ticket, sla_info):
        """Send notification when SLA is breached"""
        if not settings.EMAIL_NOTIFICATIONS_ENABLED:
            return
            
        try:
            # Send to all relevant stakeholders
            stakeholders = set()
            
            # Add assigned user
            if ticket.assigned_to:
                stakeholders.add(ticket.assigned_to)
            
            # Add company admins
            company_admins = User.objects.filter(
                company=ticket.company,
                role__in=['COMPANY_ADMIN', 'SUPERADMIN']
            )
            stakeholders.update(company_admins)
            
            # Add superadmins
            superadmins = User.objects.filter(role='SUPERADMIN')
            stakeholders.update(superadmins)
            
            for stakeholder in stakeholders:
                EmailService._send_email_to_user(
                    user=stakeholder,
                    template_name='emails/sla_breach',
                    subject=f'🚨 SLA Incumplido: {ticket.title}',
                    context={
                        'ticket': ticket,
                        'sla_info': sla_info,
                        'user': stakeholder
                    }
                )
                
        except Exception as e:
            logger.error(f"Error sending SLA breach notification: {e}")
    
    @staticmethod
    def _send_email_to_user(user, template_name, subject, context):
        """Internal method to send email to a specific user"""
        try:
            # Render HTML template
            html_content = render_to_string(f'{template_name}.html', context)
            
            # Create plain text version
            text_content = strip_tags(html_content)
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=f"{settings.EMAIL_SUBJECT_PREFIX}{subject}",
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            logger.info(f"Email sent successfully to {user.email}: {subject}")
            
        except Exception as e:
            logger.error(f"Error sending email to {user.email}: {e}")
