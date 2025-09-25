#!/usr/bin/env python
"""
Script para probar el envío de correos electrónicos en desarrollo
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from apps.users.models import User
from apps.tickets.models import Ticket

def test_basic_email():
    """Prueba básica de envío de email"""
    print("🧪 Probando envío básico de email...")
    print(f"📧 Backend configurado: {settings.EMAIL_BACKEND}")
    print(f"📨 Email por defecto: {settings.DEFAULT_FROM_EMAIL}")
    
    try:
        send_mail(
            subject='Prueba de Email - Helpdesk',
            message='Este es un email de prueba desde el sistema de helpdesk.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],
            fail_silently=False,
        )
        print("✅ Email básico enviado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error enviando email básico: {e}")
        return False

def test_html_email():
    """Prueba de envío de email HTML"""
    print("\n🧪 Probando envío de email HTML...")
    
    try:
        html_content = """
        <html>
        <body>
            <h2>Prueba de Email HTML</h2>
            <p>Este es un <strong>email de prueba</strong> con formato HTML.</p>
            <ul>
                <li>✅ Formato HTML funcionando</li>
                <li>📧 Sistema de notificaciones activo</li>
                <li>🎯 Listo para producción</li>
            </ul>
        </body>
        </html>
        """
        
        email = EmailMessage(
            subject='Prueba HTML - Helpdesk',
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['test@example.com'],
        )
        email.content_subtype = 'html'
        email.send()
        
        print("✅ Email HTML enviado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error enviando email HTML: {e}")
        return False

def test_template_email():
    """Prueba de envío usando templates"""
    print("\n🧪 Probando envío con template...")
    
    try:
        # Crear contexto de prueba
        context = {
            'user_name': 'Usuario de Prueba',
            'ticket_id': 'TEST-001',
            'ticket_title': 'Ticket de Prueba',
            'message': 'Este es un mensaje de prueba para verificar el sistema de templates.',
            'site_name': 'Helpdesk Sistema',
        }
        
        # Renderizar template (usaremos un template simple)
        html_message = f"""
        <h2>Notificación de Ticket</h2>
        <p>Hola {context['user_name']},</p>
        <p>Se ha actualizado el ticket <strong>{context['ticket_id']}</strong>:</p>
        <h3>{context['ticket_title']}</h3>
        <p>{context['message']}</p>
        <hr>
        <p>Saludos,<br>{context['site_name']}</p>
        """
        
        plain_message = strip_tags(html_message)
        
        email = EmailMessage(
            subject=f"[{context['ticket_id']}] {context['ticket_title']}",
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['test@example.com'],
        )
        email.content_subtype = 'html'
        email.send()
        
        print("✅ Email con template enviado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error enviando email con template: {e}")
        return False

def test_notification_system():
    """Prueba del sistema de notificaciones completo"""
    print("\n🧪 Probando sistema de notificaciones...")
    
    try:
        # Verificar si hay usuarios en la base de datos
        users = User.objects.all()[:3]
        if not users:
            print("⚠️  No hay usuarios en la base de datos para probar")
            return False
        
        for user in users:
            send_mail(
                subject='Prueba Sistema de Notificaciones',
                message=f'Hola {user.get_full_name() or user.username}, este es un email de prueba del sistema de notificaciones.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email] if user.email else ['test@example.com'],
                fail_silently=False,
            )
            print(f"📧 Email enviado a: {user.email or 'test@example.com'}")
        
        print("✅ Sistema de notificaciones funcionando correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en sistema de notificaciones: {e}")
        return False

def show_email_configuration():
    """Muestra la configuración actual de email"""
    print("📋 CONFIGURACIÓN ACTUAL DE EMAIL")
    print("=" * 50)
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {settings.EMAIL_HOST}")
    print(f"Puerto: {settings.EMAIL_PORT}")
    print(f"TLS: {settings.EMAIL_USE_TLS}")
    print(f"Usuario: {settings.EMAIL_HOST_USER}")
    print(f"Email por defecto: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Email admin: {settings.ADMIN_EMAIL}")
    print(f"Notificaciones habilitadas: {settings.EMAIL_NOTIFICATIONS_ENABLED}")
    print("=" * 50)

def main():
    """Función principal"""
    print("🚀 INICIANDO PRUEBAS DE EMAIL")
    print("=" * 50)
    
    show_email_configuration()
    
    # Ejecutar todas las pruebas
    tests = [
        test_basic_email,
        test_html_email,
        test_template_email,
        test_notification_system,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Mostrar resumen
    print("\n📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El sistema de email está listo.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa la configuración.")
    
    print("\n💡 CONSEJOS PARA DESARROLLO:")
    print("- Con console.EmailBackend verás los emails en la consola")
    print("- Con filebased.EmailBackend se guardan en archivos")
    print("- Para producción usa SMTP real (Gmail, SendGrid, etc.)")

if __name__ == '__main__':
    main()
