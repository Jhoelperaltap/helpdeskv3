from .models import Notification
from .email_service import EmailService
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json

def create_notification(recipient, notification_type, verb, sender=None, description=None, object_id=None):
    """
    Utility function to create notifications easily
    """
    notification = Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        verb=verb,
        description=description,
        object_id=object_id
    )
    
    send_real_time_notification(notification)
    
    return notification

def send_real_time_notification(notification):
    """Send notification via WebSocket"""
    channel_layer = get_channel_layer()
    group_name = f"notifications_{notification.recipient.id}"
    
    # Get unread count for the user
    unread_count = Notification.objects.filter(
        recipient=notification.recipient, 
        is_read=False
    ).count()
    
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'notification_message',
            'message_type': 'new_notification',
            'notification': {
                'id': notification.id,
                'verb': notification.verb,
                'description': notification.description,
                'notification_type': notification.notification_type,
                'sender': notification.sender.username if notification.sender else None,
                'created_at': notification.created_at.isoformat(),
                'is_read': notification.is_read,
            },
            'unread_count': unread_count
        }
    )

def notify_ticket_created(ticket, sender=None):
    """Create notification and send email when a ticket is created"""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # Get users who should be notified (admins and technicians)
    users_to_notify = User.objects.filter(
        role__in=['COMPANY_ADMIN', 'TECHNICIAN', 'SUPERADMIN']
    ).exclude(id=ticket.created_by.id if ticket.created_by else None)
    
    # Filter by company for company admins
    if ticket.company:
        company_users = users_to_notify.filter(company=ticket.company)
        global_users = users_to_notify.filter(role__in=['TECHNICIAN', 'SUPERADMIN'])
        users_to_notify = company_users.union(global_users)
    
    for user in users_to_notify:
        create_notification(
            recipient=user,
            sender=sender or ticket.created_by,
            notification_type='ticket_created',
            verb=f'Nuevo ticket creado: {ticket.title}',
            description=f'Se ha creado un nuevo ticket con prioridad {ticket.get_priority_display()}',
            object_id=ticket.id
        )
    
    EmailService.send_ticket_created_email(ticket)

def notify_ticket_assigned(ticket, assigned_to, sender=None):
    """Create notification and send email when a ticket is assigned"""
    create_notification(
        recipient=assigned_to,
        sender=sender,
        notification_type='ticket_assigned',
        verb=f'Te han asignado el ticket: {ticket.title}',
        description=f'Se te ha asignado un ticket con prioridad {ticket.get_priority_display()}',
        object_id=ticket.id
    )
    
    EmailService.send_ticket_updated_email(ticket, sender)

def notify_ticket_updated(ticket, sender=None):
    """Create notification and send email when a ticket is updated"""
    # Notify the ticket creator and assigned user
    users_to_notify = []
    if ticket.created_by:
        users_to_notify.append(ticket.created_by)
    if ticket.assigned_to and ticket.assigned_to != ticket.created_by:
        users_to_notify.append(ticket.assigned_to)
    
    for user in users_to_notify:
        if user != sender:  # Don't notify the person who made the update
            create_notification(
                recipient=user,
                sender=sender,
                notification_type='ticket_updated',
                verb=f'Ticket actualizado: {ticket.title}',
                description=f'El ticket ha sido actualizado',
                object_id=ticket.id
            )
    
    EmailService.send_ticket_updated_email(ticket, sender)

def notify_ticket_resolved(ticket, sender=None):
    """Create notification and send email when a ticket is resolved"""
    if ticket.created_by and ticket.created_by != sender:
        create_notification(
            recipient=ticket.created_by,
            sender=sender,
            notification_type='ticket_resolved',
            verb=f'Ticket resuelto: {ticket.title}',
            description=f'Tu ticket ha sido marcado como resuelto',
            object_id=ticket.id
        )
    
    EmailService.send_ticket_resolved_email(ticket)

def notify_message_added(ticket, message, sender):
    """Create notification and send email when a message is added to a ticket"""
    # Notify all participants except the sender
    users_to_notify = set()
    if ticket.created_by:
        users_to_notify.add(ticket.created_by)
    if ticket.assigned_to:
        users_to_notify.add(ticket.assigned_to)
    
    # Remove sender from participants
    users_to_notify.discard(sender)
    
    for user in users_to_notify:
        create_notification(
            recipient=user,
            sender=sender,
            notification_type='message_added',
            verb=f'Nuevo mensaje en: {ticket.title}',
            description=f'{sender.get_full_name() or sender.username} agregó un mensaje',
            object_id=ticket.id
        )
    
    EmailService.send_message_added_email(ticket, message, sender)

def notify_user_created(user, password=None, sender=None):
    """Send welcome email when a new user is created"""
    EmailService.send_welcome_email(user, password)
    
    # Create notification for admins
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    admins = User.objects.filter(role__in=['SUPERADMIN', 'COMPANY_ADMIN'])
    if user.company:
        admins = admins.filter(company=user.company)
    
    for admin in admins:
        if admin != sender:
            create_notification(
                recipient=admin,
                sender=sender,
                notification_type='user_created',
                verb=f'Nuevo usuario creado: {user.get_full_name() or user.username}',
                description=f'Se ha creado una nueva cuenta de usuario',
                object_id=user.id
            )
