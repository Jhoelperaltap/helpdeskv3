#!/usr/bin/env python
"""
Script para crear templates de email adicionales para el sistema
"""
import os
from pathlib import Path

def create_email_templates():
    """Crea templates adicionales para diferentes tipos de emails"""
    
    base_dir = Path(__file__).resolve().parent.parent
    templates_dir = base_dir / 'templates' / 'emails'
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    templates = {
        'escalation_notification.html': '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Escalamiento de Ticket - {{ site_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        .header { background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%); color: white; padding: 30px 20px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; font-weight: 600; }
        .content { padding: 30px 20px; }
        .alert { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; margin: 20px 0; }
        .ticket-info { background: #f8f9fa; border-left: 4px solid #dc3545; padding: 20px; margin: 20px 0; border-radius: 0 8px 8px 0; }
        .escalation-badge { background: #dc3545; color: white; padding: 8px 16px; border-radius: 20px; font-weight: 600; display: inline-block; }
        .button { display: inline-block; padding: 12px 24px; background: #dc3545; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #e9ecef; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 ESCALAMIENTO DE TICKET</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">{{ site_name|default:"Sistema Helpdesk" }}</p>
        </div>
        
        <div class="content">
            <div class="alert">
                <strong>⚠️ ATENCIÓN:</strong> Este ticket ha sido escalado automáticamente debido a que ha superado el tiempo límite de respuesta.
            </div>
            
            <p>Hola <strong>{{ user_name }}</strong>,</p>
            
            <p>El ticket <strong>{{ ticket.reference|default:ticket.id }}</strong> ha sido escalado al <span class="escalation-badge">Nivel {{ escalation_level }}</span></p>
            
            <div class="ticket-info">
                <h3>{{ ticket.title }}</h3>
                <p><strong>Empresa:</strong> {{ ticket.company.name|default:"N/A" }}</p>
                <p><strong>Prioridad:</strong> {{ ticket.get_priority_display }}</p>
                <p><strong>Tiempo transcurrido:</strong> {{ time_elapsed }}</p>
                <p><strong>Escalado de:</strong> {{ from_user.get_full_name|default:from_user.username|default:"Sistema" }}</p>
                <p><strong>Escalado a:</strong> {{ to_user.get_full_name|default:to_user.username }}</p>
            </div>
            
            <p>Por favor, revisa este ticket con urgencia y toma las acciones necesarias.</p>
            
            {% if ticket_url %}
            <div style="text-align: center;">
                <a href="{{ ticket_url }}" class="button">Ver Ticket Urgente</a>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>Este es un mensaje automático del sistema de escalamiento.</p>
            <p>Escalamiento automático activado el {{ escalation_date|date:"d/m/Y H:i" }}</p>
        </div>
    </div>
</body>
</html>''',

        'welcome_email.html': '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bienvenido - {{ site_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        .header { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px 20px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; font-weight: 600; }
        .content { padding: 30px 20px; }
        .welcome-box { background: #d4edda; border: 1px solid #c3e6cb; padding: 20px; border-radius: 6px; margin: 20px 0; text-align: center; }
        .button { display: inline-block; padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #e9ecef; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 ¡Bienvenido!</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">{{ site_name|default:"Sistema Helpdesk" }}</p>
        </div>
        
        <div class="content">
            <div class="welcome-box">
                <h2 style="margin-top: 0; color: #155724;">¡Tu cuenta ha sido creada exitosamente!</h2>
            </div>
            
            <p>Hola <strong>{{ user_name }}</strong>,</p>
            
            <p>Bienvenido al {{ site_name|default:"Sistema Helpdesk" }}. Tu cuenta ha sido configurada y ya puedes comenzar a usar el sistema.</p>
            
            <h3>Información de tu cuenta:</h3>
            <ul>
                <li><strong>Usuario:</strong> {{ username }}</li>
                <li><strong>Email:</strong> {{ email }}</li>
                <li><strong>Rol:</strong> {{ role_display }}</li>
                {% if company %}<li><strong>Empresa:</strong> {{ company }}</li>{% endif %}
            </ul>
            
            <h3>Próximos pasos:</h3>
            <ol>
                <li>Inicia sesión en el sistema</li>
                <li>Completa tu perfil</li>
                <li>Familiarízate con las funcionalidades</li>
                {% if role == 'CLIENT' %}<li>Crea tu primer ticket de soporte</li>{% endif %}
            </ol>
            
            {% if login_url %}
            <div style="text-align: center;">
                <a href="{{ login_url }}" class="button">Iniciar Sesión</a>
            </div>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>Si tienes alguna pregunta, no dudes en contactarnos.</p>
            {% if support_email %}<p>Soporte: <a href="mailto:{{ support_email }}">{{ support_email }}</a></p>{% endif %}
        </div>
    </div>
</body>
</html>''',

        'password_reset.html': '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Restablecer Contraseña - {{ site_name }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 20px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        .header { background: linear-gradient(135deg, #6f42c1 0%, #e83e8c 100%); color: white; padding: 30px 20px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; font-weight: 600; }
        .content { padding: 30px 20px; }
        .security-notice { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 6px; margin: 20px 0; }
        .button { display: inline-block; padding: 12px 24px; background: #6f42c1; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 20px 0; }
        .footer { background: #f8f9fa; padding: 20px; text-align: center; color: #6c757d; font-size: 14px; border-top: 1px solid #e9ecef; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Restablecer Contraseña</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">{{ site_name|default:"Sistema Helpdesk" }}</p>
        </div>
        
        <div class="content">
            <p>Hola <strong>{{ user_name }}</strong>,</p>
            
            <p>Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.</p>
            
            <div class="security-notice">
                <strong>🔒 Aviso de Seguridad:</strong> Si no solicitaste este cambio, puedes ignorar este email. Tu contraseña no será modificada.
            </div>
            
            <p>Para crear una nueva contraseña, haz clic en el siguiente enlace:</p>
            
            {% if reset_url %}
            <div style="text-align: center;">
                <a href="{{ reset_url }}" class="button">Restablecer Contraseña</a>
            </div>
            {% endif %}
            
            <p><strong>Este enlace expirará en {{ expiry_hours|default:"24" }} horas.</strong></p>
            
            <p>Si el botón no funciona, copia y pega el siguiente enlace en tu navegador:</p>
            <p style="word-break: break-all; background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace;">{{ reset_url }}</p>
        </div>
        
        <div class="footer">
            <p>Por razones de seguridad, este enlace solo puede usarse una vez.</p>
            <p>Si tienes problemas, contacta al soporte técnico.</p>
        </div>
    </div>
</body>
</html>'''
    }
    
    print("📧 CREANDO TEMPLATES DE EMAIL")
    print("=" * 50)
    
    created_count = 0
    for filename, content in templates.items():
        file_path = templates_dir / filename
        
        if file_path.exists():
            print(f"⚠️  {filename} ya existe, omitiendo...")
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Creado: {filename}")
            created_count += 1
    
    print(f"\n📊 RESUMEN:")
    print(f"✅ Templates creados: {created_count}")
    print(f"📁 Directorio: {templates_dir}")
    
    print(f"\n💡 CÓMO USAR LOS TEMPLATES:")
    print("1. Desde Django views:")
    print("   from django.template.loader import render_to_string")
    print("   html_content = render_to_string('emails/ticket_notification.html', context)")
    print("\n2. En las pruebas de email:")
    print("   Ve a /tickets/admin/email-test/ para probar los templates")
    
    return templates_dir

if __name__ == '__main__':
    create_email_templates()
