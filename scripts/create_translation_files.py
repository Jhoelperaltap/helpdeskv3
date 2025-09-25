#!/usr/bin/env python3
"""
Script para crear archivos de traducción para el sistema Helpdesk
"""

import os
import subprocess
import sys
from pathlib import Path

def create_translation_files():
    """Crear archivos de traducción para español e inglés"""
    
    # Obtener el directorio base del proyecto
    base_dir = Path(__file__).resolve().parent.parent
    
    print("🌍 Creando archivos de traducción para Helpdesk...")
    
    # Crear directorio locale si no existe
    locale_dir = base_dir / 'locale'
    locale_dir.mkdir(exist_ok=True)
    
    # Idiomas a crear
    languages = ['es', 'en']
    
    for lang in languages:
        print(f"📝 Creando traducción para {lang}...")
        
        # Crear directorio para el idioma
        lang_dir = locale_dir / lang / 'LC_MESSAGES'
        lang_dir.mkdir(parents=True, exist_ok=True)
        
        # Ejecutar makemessages para crear archivos .po
        try:
            subprocess.run([
                sys.executable, 'manage.py', 'makemessages', 
                '-l', lang, '--ignore=venv', '--ignore=node_modules'
            ], cwd=base_dir, check=True)
            print(f"✅ Archivo de traducción creado para {lang}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creando traducción para {lang}: {e}")
    
    # Crear archivo de traducciones personalizadas para español
    es_po_file = locale_dir / 'es' / 'LC_MESSAGES' / 'django.po'
    if es_po_file.exists():
        print("📝 Agregando traducciones personalizadas para español...")
        
        # Leer contenido actual
        with open(es_po_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Agregar traducciones personalizadas si no existen
        custom_translations = '''
# Traducciones personalizadas para Helpdesk
msgid "Dashboard"
msgstr "Panel de Control"

msgid "Tickets"
msgstr "Tickets"

msgid "Notifications"
msgstr "Notificaciones"

msgid "Administration"
msgstr "Administración"

msgid "Create User"
msgstr "Crear Usuario"

msgid "Manage Users"
msgstr "Gestionar Usuarios"

msgid "Escalation"
msgstr "Escalamiento"

msgid "Django Admin Panel"
msgstr "Panel Django Admin"

msgid "Logout"
msgstr "Cerrar Sesión"

msgid "Login"
msgstr "Iniciar Sesión"

msgid "Welcome to Helpdesk System"
msgstr "Bienvenido al Sistema Helpdesk"

msgid "Manage support tickets, monitor team performance and provide the best customer service experience."
msgstr "Gestiona tickets de soporte, monitorea el rendimiento del equipo y brinda la mejor experiencia de atención al cliente."

msgid "Create Ticket"
msgstr "Crear Ticket"

msgid "View Dashboard"
msgstr "Ver Panel de Control"

msgid "Helpdesk v3"
msgstr "Helpdesk v3"

msgid "Support System"
msgstr "Sistema de Soporte"

msgid "All rights reserved."
msgstr "Todos los derechos reservados."

msgid "Session About to Expire"
msgstr "Sesión por Expirar"

msgid "Your session will expire in"
msgstr "Tu sesión expirará en"

msgid "minutes due to inactivity."
msgstr "minutos por inactividad."

msgid "Extend Session"
msgstr "Extender Sesión"

msgid "Session extended successfully"
msgstr "Sesión extendida exitosamente"

msgid "Error extending session"
msgstr "Error al extender la sesión"

msgid "Professional Technology Services"
msgstr "Servicios Profesionales de Tecnología"

msgid "Transforming Your IT Infrastructure"
msgstr "Transformando Tu Infraestructura TI"

msgid "We are specialists in server administration, network security and comprehensive technology infrastructure management."
msgstr "Somos especialistas en administración de servidores, seguridad de redes y gestión integral de infraestructura tecnológica."

msgid "Access System"
msgstr "Acceder al Sistema"

msgid "Learn About Services"
msgstr "Conocer Servicios"

msgid "Our Services"
msgstr "Nuestros Servicios"

msgid "Server Administration"
msgstr "Administración de Servidores"

msgid "Firewall and Security"
msgstr "Firewall y Seguridad"

msgid "Network Infrastructure"
msgstr "Infraestructura de Red"

msgid "Active Directory"
msgstr "Active Directory"

msgid "Technical Support"
msgstr "Soporte Técnico"

msgid "Data Protection"
msgstr "Protección de Datos"

msgid "Why choose E&J TI?"
msgstr "¿Por qué elegir E&J TI?"

msgid "Proven Experience"
msgstr "Experiencia Comprobada"

msgid "24/7 Support"
msgstr "Soporte 24/7"

msgid "Updated Technology"
msgstr "Tecnología Actualizada"

msgid "Professional Certifications"
msgstr "Certificaciones Profesionales"

msgid "Ready to optimize your IT infrastructure?"
msgstr "¿Listo para optimizar tu infraestructura TI?"

msgid "Contact"
msgstr "Contacto"

msgid "Services"
msgstr "Servicios"

msgid "About Us"
msgstr "Nosotros"
'''
        
        # Solo agregar si no están ya presentes
        if 'msgid "Dashboard"' not in content:
            with open(es_po_file, 'a', encoding='utf-8') as f:
                f.write(custom_translations)
            print("✅ Traducciones personalizadas agregadas")
    
    # Crear archivo de traducciones para inglés
    en_po_file = locale_dir / 'en' / 'LC_MESSAGES' / 'django.po'
    if en_po_file.exists():
        print("📝 Agregando traducciones personalizadas para inglés...")
        
        # Leer contenido actual
        with open(en_po_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Agregar traducciones personalizadas para inglés
        custom_translations_en = '''
# Custom translations for Helpdesk (English)
msgid "Dashboard"
msgstr "Dashboard"

msgid "Tickets"
msgstr "Tickets"

msgid "Notifications"
msgstr "Notifications"

msgid "Administration"
msgstr "Administration"

msgid "Create User"
msgstr "Create User"

msgid "Manage Users"
msgstr "Manage Users"

msgid "Escalation"
msgstr "Escalation"

msgid "Django Admin Panel"
msgstr "Django Admin Panel"

msgid "Logout"
msgstr "Logout"

msgid "Login"
msgstr "Login"

msgid "Welcome to Helpdesk System"
msgstr "Welcome to Helpdesk System"

msgid "Manage support tickets, monitor team performance and provide the best customer service experience."
msgstr "Manage support tickets, monitor team performance and provide the best customer service experience."

msgid "Create Ticket"
msgstr "Create Ticket"

msgid "View Dashboard"
msgstr "View Dashboard"

msgid "Helpdesk v3"
msgstr "Helpdesk v3"

msgid "Support System"
msgstr "Support System"

msgid "All rights reserved."
msgstr "All rights reserved."

msgid "Session About to Expire"
msgstr "Session About to Expire"

msgid "Your session will expire in"
msgstr "Your session will expire in"

msgid "minutes due to inactivity."
msgstr "minutes due to inactivity."

msgid "Extend Session"
msgstr "Extend Session"

msgid "Session extended successfully"
msgstr "Session extended successfully"

msgid "Error extending session"
msgstr "Error extending session"

msgid "Professional Technology Services"
msgstr "Professional Technology Services"

msgid "Transforming Your IT Infrastructure"
msgstr "Transforming Your IT Infrastructure"

msgid "We are specialists in server administration, network security and comprehensive technology infrastructure management."
msgstr "We are specialists in server administration, network security and comprehensive technology infrastructure management."

msgid "Access System"
msgstr "Access System"

msgid "Learn About Services"
msgstr "Learn About Services"

msgid "Our Services"
msgstr "Our Services"

msgid "Server Administration"
msgstr "Server Administration"

msgid "Firewall and Security"
msgstr "Firewall and Security"

msgid "Network Infrastructure"
msgstr "Network Infrastructure"

msgid "Active Directory"
msgstr "Active Directory"

msgid "Technical Support"
msgstr "Technical Support"

msgid "Data Protection"
msgstr "Data Protection"

msgid "Why choose E&J TI?"
msgstr "Why choose E&J TI?"

msgid "Proven Experience"
msgstr "Proven Experience"

msgid "24/7 Support"
msgstr "24/7 Support"

msgid "Updated Technology"
msgstr "Updated Technology"

msgid "Professional Certifications"
msgstr "Professional Certifications"

msgid "Ready to optimize your IT infrastructure?"
msgstr "Ready to optimize your IT infrastructure?"

msgid "Contact"
msgstr "Contact"

msgid "Services"
msgstr "Services"

msgid "About Us"
msgstr "About Us"
'''
        
        # Solo agregar si no están ya presentes
        if 'msgid "Dashboard"' not in content:
            with open(en_po_file, 'a', encoding='utf-8') as f:
                f.write(custom_translations_en)
            print("✅ Traducciones personalizadas agregadas para inglés")
    
    # Compilar traducciones
    print("🔨 Compilando traducciones...")
    try:
        subprocess.run([
            sys.executable, 'manage.py', 'compilemessages'
        ], cwd=base_dir, check=True)
        print("✅ Traducciones compiladas exitosamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error compilando traducciones: {e}")
    
    print("\n🎉 ¡Archivos de traducción creados exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Ejecuta este script para crear los archivos de traducción")
    print("2. Reinicia el servidor Django")
    print("3. El selector de idioma aparecerá en el header")
    print("4. Los usuarios podrán cambiar entre español e inglés")

if __name__ == '__main__':
    create_translation_files()
