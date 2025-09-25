#!/usr/bin/env python
"""
Script to create database migrations for the new API models
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/app')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command

def create_migrations():
    """Create migrations for all apps"""
    print("Creating migrations for tickets app...")
    call_command('makemigrations', 'tickets', verbosity=2)
    
    print("Creating migrations for accounts app...")
    call_command('makemigrations', 'accounts', verbosity=2)
    
    print("Applying migrations...")
    call_command('migrate', verbosity=2)
    
    print("Migrations completed successfully!")

if __name__ == '__main__':
    create_migrations()
