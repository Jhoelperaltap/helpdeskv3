#!/usr/bin/env python3
"""
Script para verificar que la configuración de .env esté funcionando correctamente
"""

import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
from dotenv import load_dotenv

def main():
    print("🔍 VERIFICACIÓN DE CONFIGURACIÓN .ENV")
    print("=" * 50)
    
    # Verificar ubicación del archivo .env
    env_file = project_root / '.env'
    print(f"\n📁 Ubicación del proyecto: {project_root}")
    print(f"📄 Archivo .env esperado en: {env_file}")
    print(f"📄 ¿Archivo .env existe?: {'✅ Sí' if env_file.exists() else '❌ No'}")
    
    if env_file.exists():
        print(f"📏 Tamaño del archivo .env: {env_file.stat().st_size} bytes")
        
        # Leer contenido del .env (sin mostrar passwords)
        print("\n📋 CONTENIDO DEL ARCHIVO .ENV:")
        print("-" * 30)
        with open(env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    if 'PASSWORD' in line.upper() or 'SECRET' in line.upper():
                        key = line.split('=')[0]
                        print(f"{line_num:2d}: {key}=***OCULTO***")
                    else:
                        print(f"{line_num:2d}: {line}")
    
    # Cargar .env manualmente para comparar
    print(f"\n🔄 Cargando .env manualmente...")
    load_dotenv(env_file)
    
    # Variables de email importantes
    email_vars = {
        'EMAIL_BACKEND': os.environ.get('EMAIL_BACKEND'),
        'EMAIL_HOST': os.environ.get('EMAIL_HOST'),
        'EMAIL_PORT': os.environ.get('EMAIL_PORT'),
        'EMAIL_USE_TLS': os.environ.get('EMAIL_USE_TLS'),
        'EMAIL_HOST_USER': os.environ.get('EMAIL_HOST_USER'),
        'EMAIL_HOST_PASSWORD': '***CONFIGURADO***' if os.environ.get('EMAIL_HOST_PASSWORD') else None,
        'DEFAULT_FROM_EMAIL': os.environ.get('DEFAULT_FROM_EMAIL'),
        'DEBUG': os.environ.get('DEBUG'),
    }
    
    print(f"\n🌍 VARIABLES DE ENTORNO (desde os.environ):")
    print("-" * 40)
    for key, value in email_vars.items():
        status = "✅" if value else "❌"
        print(f"{status} {key}: {value}")
    
    print(f"\n⚙️  CONFIGURACIÓN DE DJANGO (desde settings):")
    print("-" * 45)
    django_settings = {
        'EMAIL_BACKEND': settings.EMAIL_BACKEND,
        'EMAIL_HOST': settings.EMAIL_HOST,
        'EMAIL_PORT': settings.EMAIL_PORT,
        'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
        'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
        'EMAIL_HOST_PASSWORD': '***CONFIGURADO***' if settings.EMAIL_HOST_PASSWORD else 'NO CONFIGURADO',
        'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
        'DEBUG': settings.DEBUG,
    }
    
    for key, value in django_settings.items():
        status = "✅" if value else "❌"
        print(f"{status} {key}: {value}")
    
    # Verificar discrepancias
    print(f"\n🔍 ANÁLISIS DE DISCREPANCIAS:")
    print("-" * 30)
    
    discrepancies = []
    
    # Comparar EMAIL_BACKEND
    env_backend = os.environ.get('EMAIL_BACKEND')
    django_backend = settings.EMAIL_BACKEND
    
    if env_backend != django_backend:
        discrepancies.append(f"EMAIL_BACKEND: .env='{env_backend}' vs Django='{django_backend}'")
    
    # Comparar EMAIL_HOST_USER
    env_user = os.environ.get('EMAIL_HOST_USER')
    django_user = settings.EMAIL_HOST_USER
    
    if env_user != django_user:
        discrepancies.append(f"EMAIL_HOST_USER: .env='{env_user}' vs Django='{django_user}'")
    
    if discrepancies:
        print("❌ Se encontraron discrepancias:")
        for disc in discrepancies:
            print(f"   • {disc}")
    else:
        print("✅ No hay discrepancias entre .env y Django settings")
    
    # Diagnóstico final
    print(f"\n📊 DIAGNÓSTICO FINAL:")
    print("-" * 20)
    
    if not env_file.exists():
        print("❌ PROBLEMA: El archivo .env no existe")
        print("   SOLUCIÓN: Crear archivo .env en la raíz del proyecto")
        return False
    
    if not os.environ.get('EMAIL_BACKEND'):
        print("❌ PROBLEMA: EMAIL_BACKEND no está configurado en .env")
        print("   SOLUCIÓN: Agregar EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend")
        return False
    
    if not os.environ.get('EMAIL_HOST_USER'):
        print("❌ PROBLEMA: EMAIL_HOST_USER no está configurado en .env")
        print("   SOLUCIÓN: Agregar EMAIL_HOST_USER=tu_email@gmail.com")
        return False
    
    if not os.environ.get('EMAIL_HOST_PASSWORD'):
        print("❌ PROBLEMA: EMAIL_HOST_PASSWORD no está configurado en .env")
        print("   SOLUCIÓN: Agregar EMAIL_HOST_PASSWORD=tu_app_password")
        return False
    
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        print("⚠️  ADVERTENCIA: Usando console backend")
        print("   Para enviar emails reales, asegúrate de que EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend")
        return False
    
    print("✅ ¡Configuración correcta! El sistema debería poder enviar emails reales.")
    return True

if __name__ == '__main__':
    success = main()
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 ¡TODO LISTO! Puedes probar el envío de emails desde la interfaz web.")
        print("   Ve a: Admin → Pruebas Email")
    else:
        print("🔧 ACCIÓN REQUERIDA: Corrige los problemas encontrados y vuelve a ejecutar este script.")
    
    print("\n💡 PASOS SIGUIENTES:")
    print("1. Corrige cualquier problema encontrado")
    print("2. Reinicia el servidor de Django")
    print("3. Ve a la página de Pruebas Email en el admin")
    print("4. Envía un email de prueba")
