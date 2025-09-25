from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.notifications.email_service import EmailService
from apps.tickets.models import Ticket

User = get_user_model()

class Command(BaseCommand):
    help = 'Send test email to verify email configuration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test email to',
            required=True
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['welcome', 'ticket_created', 'ticket_updated'],
            default='welcome',
            help='Type of test email to send'
        )
    
    def handle(self, *args, **options):
        email = options['email']
        email_type = options['type']
        
        try:
            # Create a test user for email testing
            test_user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': 'test_user',
                    'first_name': 'Test',
                    'last_name': 'User',
                    'role': 'EMPLOYEE'
                }
            )
            
            if email_type == 'welcome':
                EmailService.send_welcome_email(test_user, 'temp_password_123')
                self.stdout.write(
                    self.style.SUCCESS(f'Welcome email sent successfully to {email}')
                )
                
            elif email_type == 'ticket_created':
                # Find a test ticket or create one
                ticket = Ticket.objects.first()
                if ticket:
                    EmailService.send_ticket_created_email(ticket)
                    self.stdout.write(
                        self.style.SUCCESS(f'Ticket created email sent successfully to {email}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('No tickets found to send test email')
                    )
                    
            elif email_type == 'ticket_updated':
                ticket = Ticket.objects.first()
                if ticket:
                    EmailService.send_ticket_updated_email(ticket, test_user)
                    self.stdout.write(
                        self.style.SUCCESS(f'Ticket updated email sent successfully to {email}')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('No tickets found to send test email')
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending test email: {e}')
            )
