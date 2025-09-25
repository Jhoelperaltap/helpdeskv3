#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    if 'runserver' in sys.argv:
        print("Para soporte de WebSockets, usa: python manage.py runserver --settings=config.settings")
        print("O instala daphne y usa: daphne -p 8000 config.asgi:application")
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
