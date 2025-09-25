import os
import django
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def create_translation_files():
    """Crear archivos de traducción manualmente sin gettext"""
    
    print("🌍 Creando archivos de traducción manuales para Helpdesk...")
    
    # Crear directorios de locale
    base_dir = Path(__file__).resolve().parent.parent
    locale_dir = base_dir / 'locale'
    
    # Crear directorios para cada idioma
    for lang in ['es', 'en']:
        lang_dir = locale_dir / lang / 'LC_MESSAGES'
        lang_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Creado directorio: {lang_dir}")
    
    # Traducciones principales del sistema
    translations = {
        # Navegación y menús
        "Home": {"es": "Inicio", "en": "Home"},
        "Dashboard": {"es": "Panel", "en": "Dashboard"},
        "Tickets": {"es": "Tickets", "en": "Tickets"},
        "Users": {"es": "Usuarios", "en": "Users"},
        "Settings": {"es": "Configuración", "en": "Settings"},
        "Login": {"es": "Iniciar Sesión", "en": "Login"},
        "Logout": {"es": "Cerrar Sesión", "en": "Logout"},
        "Profile": {"es": "Perfil", "en": "Profile"},
        
        # Página principal
        "Welcome to TI Support Platform": {"es": "Bienvenido a la Plataforma de Soporte TI", "en": "Welcome to TI Support Platform"},
        "Your comprehensive solution for IT support management": {"es": "Tu solución integral para la gestión de soporte TI", "en": "Your comprehensive solution for IT support management"},
        "Get Started": {"es": "Comenzar", "en": "Get Started"},
        "Learn More": {"es": "Saber Más", "en": "Learn More"},
        "Contact Us": {"es": "Contáctanos", "en": "Contact Us"},
        
        # Tickets
        "Create Ticket": {"es": "Crear Ticket", "en": "Create Ticket"},
        "View Tickets": {"es": "Ver Tickets", "en": "View Tickets"},
        "Ticket Status": {"es": "Estado del Ticket", "en": "Ticket Status"},
        "Priority": {"es": "Prioridad", "en": "Priority"},
        "Assigned to": {"es": "Asignado a", "en": "Assigned to"},
        "Created": {"es": "Creado", "en": "Created"},
        "Updated": {"es": "Actualizado", "en": "Updated"},
        "Description": {"es": "Descripción", "en": "Description"},
        "Subject": {"es": "Asunto", "en": "Subject"},
        
        # Estados
        "Open": {"es": "Abierto", "en": "Open"},
        "In Progress": {"es": "En Progreso", "en": "In Progress"},
        "Resolved": {"es": "Resuelto", "en": "Resolved"},
        "Closed": {"es": "Cerrado", "en": "Closed"},
        
        # Prioridades
        "Low": {"es": "Baja", "en": "Low"},
        "Medium": {"es": "Media", "en": "Medium"},
        "High": {"es": "Alta", "en": "High"},
        "Critical": {"es": "Crítica", "en": "Critical"},
        
        # Formularios
        "Submit": {"es": "Enviar", "en": "Submit"},
        "Cancel": {"es": "Cancelar", "en": "Cancel"},
        "Save": {"es": "Guardar", "en": "Save"},
        "Delete": {"es": "Eliminar", "en": "Delete"},
        "Edit": {"es": "Editar", "en": "Edit"},
        "Search": {"es": "Buscar", "en": "Search"},
        "Filter": {"es": "Filtrar", "en": "Filter"},
        
        # Mensajes
        "Success": {"es": "Éxito", "en": "Success"},
        "Error": {"es": "Error", "en": "Error"},
        "Warning": {"es": "Advertencia", "en": "Warning"},
        "Information": {"es": "Información", "en": "Information"},
        
        # Email Test
        "Email Configuration Test": {"es": "Prueba de Configuración de Email", "en": "Email Configuration Test"},
        "Test Connection": {"es": "Probar Conexión", "en": "Test Connection"},
        "Send Test Email": {"es": "Enviar Email de Prueba", "en": "Send Test Email"},
        "SMTP Configuration": {"es": "Configuración SMTP", "en": "SMTP Configuration"},
        "Connection Status": {"es": "Estado de Conexión", "en": "Connection Status"},
        "Connected": {"es": "Conectado", "en": "Connected"},
        "Disconnected": {"es": "Desconectado", "en": "Disconnected"},
        "Testing...": {"es": "Probando...", "en": "Testing..."},
        
        # Administración
        "Administration": {"es": "Administración", "en": "Administration"},
        "User Management": {"es": "Gestión de Usuarios", "en": "User Management"},
        "System Settings": {"es": "Configuración del Sistema", "en": "System Settings"},
        "Email Tests": {"es": "Pruebas de Email", "en": "Email Tests"},
        
        # Fechas y tiempo
        "Today": {"es": "Hoy", "en": "Today"},
        "Yesterday": {"es": "Ayer", "en": "Yesterday"},
        "Last week": {"es": "Semana pasada", "en": "Last week"},
        "Last month": {"es": "Mes pasado", "en": "Last month"},
    }
    
    # Crear archivo .po para español
    es_po_content = '''# Spanish translations for Helpdesk
# Copyright (C) 2024
# This file is distributed under the same license as the Helpdesk package.
#
msgid ""
msgstr ""
"Project-Id-Version: Helpdesk 1.0\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2024-01-01 12:00+0000\\n"
"PO-Revision-Date: 2024-01-01 12:00+0000\\n"
"Last-Translator: Auto Generated\\n"
"Language-Team: Spanish\\n"
"Language: es\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

'''
    
    # Crear archivo .po para inglés
    en_po_content = '''# English translations for Helpdesk
# Copyright (C) 2024
# This file is distributed under the same license as the Helpdesk package.
#
msgid ""
msgstr ""
"Project-Id-Version: Helpdesk 1.0\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2024-01-01 12:00+0000\\n"
"PO-Revision-Date: 2024-01-01 12:00+0000\\n"
"Last-Translator: Auto Generated\\n"
"Language-Team: English\\n"
"Language: en\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

'''
    
    # Agregar traducciones a los archivos .po
    for msgid, translations_dict in translations.items():
        # Para español
        es_po_content += f'msgid "{msgid}"\n'
        es_po_content += f'msgstr "{translations_dict["es"]}"\n\n'
        
        # Para inglés
        en_po_content += f'msgid "{msgid}"\n'
        en_po_content += f'msgstr "{translations_dict["en"]}"\n\n'
    
    # Escribir archivos .po
    es_po_file = locale_dir / 'es' / 'LC_MESSAGES' / 'django.po'
    en_po_file = locale_dir / 'en' / 'LC_MESSAGES' / 'django.po'
    
    with open(es_po_file, 'w', encoding='utf-8') as f:
        f.write(es_po_content)
    print(f"✅ Creado: {es_po_file}")
    
    with open(en_po_file, 'w', encoding='utf-8') as f:
        f.write(en_po_content)
    print(f"✅ Creado: {en_po_file}")
    
    # Crear archivos .mo compilados manualmente
    try:
        import polib
        
        # Compilar español
        po_es = polib.pofile(str(es_po_file))
        po_es.save_as_mofile(str(locale_dir / 'es' / 'LC_MESSAGES' / 'django.mo'))
        print(f"✅ Compilado: django.mo (es)")
        
        # Compilar inglés
        po_en = polib.pofile(str(en_po_file))
        po_en.save_as_mofile(str(locale_dir / 'en' / 'LC_MESSAGES' / 'django.mo'))
        print(f"✅ Compilado: django.mo (en)")
        
    except ImportError:
        print("⚠️  polib no está instalado. Instalando...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'polib'])
        
        import polib
        
        # Compilar español
        po_es = polib.pofile(str(es_po_file))
        po_es.save_as_mofile(str(locale_dir / 'es' / 'LC_MESSAGES' / 'django.mo'))
        print(f"✅ Compilado: django.mo (es)")
        
        # Compilar inglés
        po_en = polib.pofile(str(en_po_file))
        po_en.save_as_mofile(str(locale_dir / 'en' / 'LC_MESSAGES' / 'django.mo'))
        print(f"✅ Compilado: django.mo (en)")
    
    print("\n🎉 ¡Archivos de traducción creados exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Reinicia el servidor Django")
    print("2. El selector de idioma aparecerá en el header")
    print("3. Los usuarios podrán cambiar entre español e inglés")
    print("4. Las traducciones se aplicarán automáticamente")

if __name__ == "__main__":
    create_translation_files()
