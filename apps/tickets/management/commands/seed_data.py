from django.core.management.base import BaseCommand
from apps.companies.models import Company
from apps.users.models import User
from apps.tickets.models import Ticket
import uuid

class Command(BaseCommand):
    help = 'Seed database with sample companies, users and tickets'

    def handle(self, *args, **options):
        if Company.objects.exists():
            self.stdout.write(self.style.WARNING('Data may already exist. Exiting.'))
            return
        c = Company.objects.create(name='Acme Corp', slug='acme')
        admin = User.objects.create_user(username='admin_acme', email='admin@acme.local', password='admin123', role='COMPANY_ADMIN', company=c)
        emp = User.objects.create_user(username='user1', email='user1@acme.local', password='user123', role='EMPLOYEE', company=c)
        tech = User.objects.create_user(username='tech1', email='tech1@platform.local', password='tech123', role='TECHNICIAN')
        for i in range(5):
            Ticket.objects.create(reference='TKT-'+uuid.uuid4().hex[:6].upper(), title=f'Sample ticket {i+1}', description='Descripción de ejemplo', company=c, created_by=emp)
        self.stdout.write(self.style.SUCCESS('Seed data created.'))
