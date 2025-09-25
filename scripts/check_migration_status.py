#!/usr/bin/env python
"""
Script para verificar el estado actual de las migraciones.
"""

import os
import sys
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_migration_status():
    """Verifica el estado de las migraciones en la base de datos"""
    
    print("🔍 Verificando estado de migraciones...\n")
    
    with connection.cursor() as cursor:
        try:
            # Verificar si existe la tabla django_migrations
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='django_migrations'
            """)
            
            if not cursor.fetchone():
                print("❌ La tabla django_migrations no existe")
                return
            
            # Obtener todas las migraciones aplicadas
            cursor.execute("""
                SELECT app, name, applied 
                FROM django_migrations 
                WHERE app IN ('companies', 'tickets')
                ORDER BY app, name
            """)
            
            migrations = cursor.fetchall()
            
            if not migrations:
                print("⚠️  No se encontraron migraciones para companies o tickets")
                return
            
            print("📋 Migraciones aplicadas:")
            for app, name, applied in migrations:
                status = "✅" if applied else "❌"
                print(f"  {status} {app}.{name}")
                
        except Exception as e:
            print(f"❌ Error al verificar migraciones: {e}")

if __name__ == '__main__':
    check_migration_status()
