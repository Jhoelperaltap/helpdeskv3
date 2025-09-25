import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('helpdesk')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': 86400.0,  # Run daily (24 hours)
    },
    'send-daily-summary': {
        'task': 'apps.notifications.tasks.send_daily_summary',
        'schedule': 86400.0,  # Run daily
        'options': {'expires': 3600}  # Expire after 1 hour if not executed
    },
    'process-ticket-escalations': {
        'task': 'apps.tickets.tasks.process_ticket_escalations',
        'schedule': 900.0,  # Run every 15 minutes
        'options': {'expires': 600}  # Expire after 10 minutes if not executed
    },
    'update-escalation-times': {
        'task': 'apps.tickets.tasks.update_ticket_escalation_times',
        'schedule': 3600.0,  # Run every hour
        'options': {'expires': 1800}  # Expire after 30 minutes if not executed
    },
    'generate-escalation-report': {
        'task': 'apps.tickets.tasks.generate_escalation_report',
        'schedule': 86400.0,  # Run daily
        'options': {'expires': 3600}  # Expire after 1 hour if not executed
    },
    'send-escalation-warnings': {
        'task': 'apps.notifications.tasks.send_escalation_warnings',
        'schedule': 1800.0,  # Run every 30 minutes
        'options': {'expires': 900}  # Expire after 15 minutes if not executed
    },
    'send-escalation-summary-reports': {
        'task': 'apps.notifications.tasks.send_escalation_summary_reports',
        'schedule': 86400.0,  # Run daily at midnight
        'options': {'expires': 3600}  # Expire after 1 hour if not executed
    },
    'check-sla-breaches': {
        'task': 'apps.notifications.tasks.check_sla_breaches',
        'schedule': 3600.0,  # Run every hour
        'options': {'expires': 1800}  # Expire after 30 minutes if not executed
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
