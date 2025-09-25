#!/usr/bin/env python
"""
Script para configurar diferentes backends de email para desarrollo
"""
import os
from pathlib import Path

def create_env_file_with_email_config():
    """Crea archivo .env con diferentes configuraciones de email"""
    
    base_dir = Path(__file__).resolve().parent.parent
    env_file = base_dir / '.env'
    
    # Configuraciones de email para desarrollo
    email_configs = {
        'console': {
            'EMAIL_BACKEND': 'django.core.mail.backends.console.EmailBackend',
            'description': 'Los emails se muestran en la consola del servidor'
        },
        'file': {
            'EMAIL_BACKEND': 'django.core.mail.backends.filebased.EmailBackend',
            'EMAIL_FILE_PATH': str(base_dir / 'sent_emails'),
            'description': 'Los emails se guardan en archivos en la carpeta sent_emails/'
        },
        'dummy': {
            'EMAIL_BACKEND': 'django.core.mail.backends.dummy.EmailBackend',
            'description': 'Los emails se descartan (útil para testing)'
        },
        'smtp_gmail': {
            'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'EMAIL_HOST': 'smtp.gmail.com',
            'EMAIL_PORT': '587',
            'EMAIL_USE_TLS': 'True',
            'EMAIL_HOST_USER': 'tu-email@gmail.com',
            'EMAIL_HOST_PASSWORD': 'tu-app-password',
            'description': 'Configuración para Gmail (requiere App Password)'
        },
        'smtp_outlook': {
            'EMAIL_BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'EMAIL_HOST': 'smtp-mail.outlook.com',
            'EMAIL_PORT': '587',
            'EMAIL_USE_TLS': 'True',
            'EMAIL_HOST_USER': 'tu-email@outlook.com',
            'EMAIL_HOST_PASSWORD': 'tu-password',
            'description': 'Configuración para Outlook/Hotmail'
        }
    }
    
    print("🔧 CONFIGURADOR DE EMAIL PARA DESARROLLO")
    print("=" * 50)
    print("Selecciona el backend de email que quieres usar:")
    print()
    
    for i, (key, config) in enumerate(email_configs.items(), 1):
        print(f"{i}. {key.upper()}")
        print(f"   {config['description']}")
        print()
    
    while True:
        try:
            choice = int(input("Selecciona una opción (1-6): ")) - 1
            if 0 <= choice < len(email_configs):
                break
            else:
                print("❌ Opción no válida. Intenta de nuevo.")
        except ValueError:
            print("❌ Por favor ingresa un número válido.")
    
    selected_key = list(email_configs.keys())[choice]
    selected_config = email_configs[selected_key]
    
    print(f"\n✅ Seleccionaste: {selected_key.upper()}")
    print(f"📝 {selected_config['description']}")
    
    # Crear contenido del archivo .env
    env_content = [
        "# Configuración de desarrollo para Django Helpdesk",
        "# Generado automáticamente por setup_email_backends.py",
        "",
        "# Configuración básica",
        "DEBUG=True",
        "SECRET_KEY=django-insecure-dev-key-change-in-production",
        "ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0",
        "",
        "# Base de datos (SQLite para desarrollo)",
        "DATABASE_URL=sqlite:///db.sqlite3",
        "",
        f"# Configuración de Email - {selected_key.upper()}",
        f"# {selected_config['description']}",
    ]
    
    # Agregar configuraciones específicas del backend seleccionado
    for key, value in selected_config.items():
        if key != 'description':
            env_content.append(f"{key}={value}")
    
    # Configuraciones adicionales de email
    env_content.extend([
        "",
        "# Configuraciones adicionales de email",
        "DEFAULT_FROM_EMAIL=helpdesk@tuempresa.com",
        "ADMIN_EMAIL=admin@tuempresa.com",
        "EMAIL_NOTIFICATIONS_ENABLED=True",
        "EMAIL_SUBJECT_PREFIX=[Helpdesk] ",
        "",
        "# Configuración de Celery (Redis para desarrollo)",
        "CELERY_BROKER_URL=redis://localhost:6379/1",
        "CELERY_RESULT_BACKEND=redis://localhost:6379/1",
        "",
        "# Configuración de Channels (Redis para desarrollo)",
        "REDIS_URL=redis://localhost:6379",
    ])
    
    # Escribir archivo .env
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(env_content))
    
    print(f"\n📁 Archivo .env creado en: {env_file}")
    
    # Crear directorio para emails si se seleccionó file backend
    if selected_key == 'file':
        email_dir = base_dir / 'sent_emails'
        email_dir.mkdir(exist_ok=True)
        print(f"📁 Directorio para emails creado en: {email_dir}")
    
    # Mostrar instrucciones adicionales
    print("\n📋 INSTRUCCIONES:")
    print("=" * 50)
    
    if selected_key == 'console':
        print("• Los emails aparecerán en la consola donde ejecutas 'python manage.py runserver'")
        print("• Ideal para desarrollo y debugging")
        
    elif selected_key == 'file':
        print("• Los emails se guardarán como archivos en la carpeta 'sent_emails/'")
        print("• Puedes abrir los archivos para ver el contenido de los emails")
        
    elif selected_key == 'dummy':
        print("• Los emails se descartan completamente")
        print("• Útil para testing automatizado")
        
    elif selected_key in ['smtp_gmail', 'smtp_outlook']:
        print("• ⚠️  IMPORTANTE: Debes configurar las credenciales reales:")
        print(f"  - Edita el archivo .env y cambia EMAIL_HOST_USER y EMAIL_HOST_PASSWORD")
        if selected_key == 'smtp_gmail':
            print("  - Para Gmail, usa un 'App Password' en lugar de tu contraseña normal")
            print("  - Habilita la autenticación de 2 factores y genera un App Password")
        print("• Los emails se enviarán realmente a las direcciones especificadas")
    
    print("\n🚀 PRÓXIMOS PASOS:")
    print("1. Reinicia el servidor de Django: python manage.py runserver")
    print("2. Ve a /tickets/admin/email-test/ para probar el envío de emails")
    print("3. Ejecuta: python scripts/test_email_sending.py para pruebas desde consola")
    
    return env_file

def show_current_config():
    """Muestra la configuración actual de email"""
    import django
    import sys
    from pathlib import Path
    
    # Configurar Django
    base_dir = Path(__file__).resolve().parent.parent
    sys.path.append(str(base_dir))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    from django.conf import settings
    
    print("📋 CONFIGURACIÓN ACTUAL DE EMAIL")
    print("=" * 50)
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {getattr(settings, 'EMAIL_HOST', 'No configurado')}")
    print(f"Puerto: {getattr(settings, 'EMAIL_PORT', 'No configurado')}")
    print(f"TLS: {getattr(settings, 'EMAIL_USE_TLS', 'No configurado')}")
    print(f"Usuario: {getattr(settings, 'EMAIL_HOST_USER', 'No configurado')}")
    print(f"Email por defecto: {settings.DEFAULT_FROM_EMAIL}")
    print(f"Email admin: {settings.ADMIN_EMAIL}")
    print(f"Notificaciones: {settings.EMAIL_NOTIFICATIONS_ENABLED}")

def main():
    """Función principal"""
    print("🚀 CONFIGURADOR DE EMAIL PARA DESARROLLO")
    print("=" * 50)
    print("1. Configurar nuevo backend de email")
    print("2. Mostrar configuración actual")
    print("3. Salir")
    
    while True:
        try:
            choice = int(input("\nSelecciona una opción (1-3): "))
            if choice == 1:
                create_env_file_with_email_config()
                break
            elif choice == 2:
                show_current_config()
                break
            elif choice == 3:
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción no válida. Intenta de nuevo.")
        except ValueError:
            print("❌ Por favor ingresa un número válido.")
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break

if __name__ == '__main__':
    main()
