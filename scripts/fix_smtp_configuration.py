#!/usr/bin/env python3
"""
Script para verificar y corregir la configuración SMTP de Django
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

def main():
    print("🔧 Verificando configuración SMTP...")
    print("=" * 50)
    
    # Verificar archivo .env
    env_file = project_root / '.env'
    if not env_file.exists():
        print(f"❌ Archivo .env no encontrado en: {env_file}")
        print("📝 Creando archivo .env de ejemplo...")
        
        env_content = """# Configuración de Email SMTP
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password_aqui
DEFAULT_FROM_EMAIL=tu_email@gmail.com
ADMIN_EMAIL=tu_email@gmail.com
EMAIL_NOTIFICATIONS_ENABLED=True

# Configuración de Debug
DEBUG=True
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Archivo .env creado en: {env_file}")
        print("⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales reales")
        return
    
    print(f"✅ Archivo .env encontrado: {env_file}")
    
    # Leer variables del .env
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
    
    print(f"📋 Variables encontradas en .env: {len(env_vars)}")
    
    # Verificar variables críticas
    critical_vars = [
        'EMAIL_BACKEND',
        'EMAIL_HOST',
        'EMAIL_HOST_USER', 
        'EMAIL_HOST_PASSWORD'
    ]
    
    missing_vars = []
    for var in critical_vars:
        if var not in env_vars or not env_vars[var]:
            missing_vars.append(var)
        else:
            # Ocultar password para mostrar
            display_value = env_vars[var]
            if 'PASSWORD' in var and display_value:
                display_value = '*' * len(display_value)
            print(f"  ✅ {var} = {display_value}")
    
    if missing_vars:
        print(f"❌ Variables faltantes en .env: {missing_vars}")
        return
    
    # Verificar configuración de Django
    print("\n🔍 Verificando configuración de Django...")
    
    from django.conf import settings
    
    django_config = {
        'EMAIL_BACKEND': settings.EMAIL_BACKEND,
        'EMAIL_HOST': settings.EMAIL_HOST,
        'EMAIL_PORT': settings.EMAIL_PORT,
        'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
        'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
        'EMAIL_HOST_PASSWORD': bool(settings.EMAIL_HOST_PASSWORD),
        'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
    }
    
    for key, value in django_config.items():
        if 'PASSWORD' in key:
            display_value = '✅ Configurado' if value else '❌ No configurado'
        else:
            display_value = value
        print(f"  Django {key}: {display_value}")
    
    # Verificar que Django esté usando SMTP
    if settings.EMAIL_BACKEND != 'django.core.mail.backends.smtp.EmailBackend':
        print(f"⚠️  Django no está usando SMTP backend!")
        print(f"   Actual: {settings.EMAIL_BACKEND}")
        print(f"   Esperado: django.core.mail.backends.smtp.EmailBackend")
        
        # Verificar si la variable está en el .env
        if env_vars.get('EMAIL_BACKEND') == 'django.core.mail.backends.smtp.EmailBackend':
            print("❌ El .env tiene SMTP pero Django no lo está usando")
            print("💡 Posibles soluciones:")
            print("   1. Reinicia el servidor de Django")
            print("   2. Verifica que python-dotenv esté instalado")
            print("   3. Verifica que load_dotenv() esté en settings.py")
        return
    
    # Probar conexión SMTP
    print("\n📧 Probando conexión SMTP...")
    
    try:
        from django.core.mail import get_connection
        
        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
        )
        
        # Intentar abrir conexión
        connection.open()
        print("✅ Conexión SMTP exitosa!")
        connection.close()
        
        # Probar envío real
        print("\n📤 Probando envío de email real...")
        
        from django.core.mail import send_mail
        
        test_result = send_mail(
            subject='[Helpdesk] Prueba de Configuración SMTP',
            message=f"""
¡Configuración SMTP exitosa!

Este email confirma que:
✅ Django está usando el backend SMTP correcto
✅ Las credenciales de Gmail son válidas  
✅ La conexión TLS funciona correctamente
✅ El sistema puede enviar emails reales

Configuración utilizada:
- Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}
- Usuario: {settings.EMAIL_HOST_USER}
- TLS: {'Habilitado' if settings.EMAIL_USE_TLS else 'Deshabilitado'}

¡Todo listo para producción!

Sistema Helpdesk
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Enviar a ti mismo
            fail_silently=False,
        )
        
        if test_result == 1:
            print(f"✅ Email de prueba enviado exitosamente a {settings.EMAIL_HOST_USER}")
            print("📬 Revisa tu bandeja de entrada para confirmar")
        else:
            print("❌ El email no se pudo enviar")
            
    except Exception as e:
        print(f"❌ Error en conexión SMTP: {str(e)}")
        print("\n💡 Posibles soluciones:")
        print("   1. Verifica que EMAIL_HOST_USER sea correcto")
        print("   2. Verifica que EMAIL_HOST_PASSWORD sea una App Password válida")
        print("   3. Asegúrate de que la autenticación de 2 factores esté habilitada en Gmail")
        print("   4. Genera una nueva App Password en Gmail")
        return
    
    print("\n🎉 ¡Configuración SMTP completamente funcional!")
    print("💡 Ahora puedes usar las pruebas de email desde la interfaz web")

if __name__ == '__main__':
    main()
