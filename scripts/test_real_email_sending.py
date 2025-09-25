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
import traceback

def test_email_configuration():
    """Verifica la configuración actual de email"""
    print("=== CONFIGURACIÓN DE EMAIL ===")
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {settings.EMAIL_HOST}")
    print(f"Puerto: {settings.EMAIL_PORT}")
    print(f"TLS: {settings.EMAIL_USE_TLS}")
    print(f"Usuario: {settings.EMAIL_HOST_USER}")
    print(f"Password configurado: {'Sí' if settings.EMAIL_HOST_PASSWORD else 'No'}")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Admin Email: {settings.ADMIN_EMAIL}")
    print()

def send_test_email(recipient_email):
    """Envía un email de prueba real"""
    try:
        print(f"Enviando email de prueba a: {recipient_email}")
        
        # Email básico
        subject = '[Helpdesk] Prueba de Email - Configuración SMTP'
        message = """
        ¡Hola!
        
        Este es un email de prueba del sistema Helpdesk.
        
        Si recibes este mensaje, significa que la configuración SMTP está funcionando correctamente.
        
        Detalles de la configuración:
        - Backend: SMTP
        - Host: Gmail SMTP
        - Puerto: 587
        - TLS: Habilitado
        
        ¡Saludos!
        Sistema Helpdesk
        """
        
        result = send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        if result:
            print("✅ Email básico enviado exitosamente!")
        else:
            print("❌ Error: No se pudo enviar el email básico")
            
        return result
        
    except Exception as e:
        print(f"❌ Error enviando email: {str(e)}")
        print("Detalles del error:")
        traceback.print_exc()
        return False

def send_html_test_email(recipient_email):
    """Envía un email HTML de prueba"""
    try:
        print(f"Enviando email HTML de prueba a: {recipient_email}")
        
        # Crear email HTML
        subject = '[Helpdesk] Prueba de Email HTML - SMTP'
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Prueba Email Helpdesk</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #4f46e5; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9fafb; }
                .footer { padding: 20px; text-align: center; color: #666; }
                .success { color: #059669; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Prueba de Email HTML</h1>
                </div>
                <div class="content">
                    <h2>¡Configuración SMTP Exitosa!</h2>
                    <p>Si estás viendo este email, significa que:</p>
                    <ul>
                        <li>✅ La configuración SMTP está funcionando</li>
                        <li>✅ Gmail está permitiendo el envío</li>
                        <li>✅ Las credenciales son correctas</li>
                        <li>✅ El sistema puede enviar emails HTML</li>
                    </ul>
                    <p class="success">¡Todo está listo para producción!</p>
                </div>
                <div class="footer">
                    <p>Sistema Helpdesk - Prueba de Configuración</p>
                    <p>Enviado desde: {}</p>
                </div>
            </div>
        </body>
        </html>
        """.format(settings.DEFAULT_FROM_EMAIL)
        
        text_content = strip_tags(html_content)
        
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.content_subtype = "html"
        
        result = email.send()
        
        if result:
            print("✅ Email HTML enviado exitosamente!")
        else:
            print("❌ Error: No se pudo enviar el email HTML")
            
        return result
        
    except Exception as e:
        print(f"❌ Error enviando email HTML: {str(e)}")
        traceback.print_exc()
        return False

def main():
    print("🚀 PRUEBA DE ENVÍO DE EMAILS REALES")
    print("=" * 50)
    
    # Verificar configuración
    test_email_configuration()
    
    # Verificar que tenemos configuración SMTP
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        print("⚠️  ADVERTENCIA: Estás usando console backend.")
        print("   Los emails se mostrarán en la consola, no se enviarán realmente.")
        print("   Para enviar emails reales, cambia EMAIL_BACKEND en tu .env")
        print()
    
    # Solicitar email de destino
    recipient = input("Ingresa el email donde quieres recibir la prueba: ").strip()
    
    if not recipient:
        print("❌ Email requerido para la prueba")
        return
    
    print(f"\n📧 Enviando emails de prueba a: {recipient}")
    print("-" * 40)
    
    # Enviar email básico
    success1 = send_test_email(recipient)
    
    print()
    
    # Enviar email HTML
    success2 = send_html_test_email(recipient)
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS")
    print(f"Email básico: {'✅ Enviado' if success1 else '❌ Falló'}")
    print(f"Email HTML: {'✅ Enviado' if success2 else '❌ Falló'}")
    
    if success1 and success2:
        print("\n🎉 ¡TODAS LAS PRUEBAS EXITOSAS!")
        print("Tu configuración SMTP está funcionando perfectamente.")
        print("Revisa tu bandeja de entrada (y spam) para ver los emails.")
    else:
        print("\n⚠️  Algunas pruebas fallaron.")
        print("Revisa la configuración en tu archivo .env")
        print("Especialmente EMAIL_HOST_USER y EMAIL_HOST_PASSWORD")

if __name__ == "__main__":
    main()
