# Guía de Despliegue en Hostinger

## Pasos para desplegar en Hostinger

### 1. Preparar archivos localmente
\`\`\`bash
# Ejecutar script de preparación
python scripts/deploy_production.py
\`\`\`

### 2. Configurar base de datos
- Crear base de datos PostgreSQL en el panel de Hostinger
- Anotar: nombre de BD, usuario, contraseña, host

### 3. Subir archivos
- Comprimir todo el proyecto (excepto venv/, __pycache__/, .git/)
- Subir al directorio public_html de Hostinger
- Extraer archivos

### 4. Configurar variables de entorno
- Crear archivo `.env` basado en `.env.example`
- Configurar DATABASE_URL con datos de tu BD
- Generar SECRET_KEY nueva para producción
- Configurar ALLOWED_HOSTS con tu dominio

### 5. Configurar Python en Hostinger
- Ir a Panel de Control > Python
- Seleccionar versión Python 3.8+
- Configurar directorio de aplicación
- Instalar dependencias: `pip install -r requirements.txt`

### 6. Configurar aplicación
\`\`\`bash
# En terminal de Hostinger
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
\`\`\`

### 7. Configurar servidor web
- El archivo `passenger_wsgi.py` ya está configurado
- El archivo `.htaccess` maneja las redirecciones

### 8. Configurar tareas programadas (Celery)
- En Panel de Control > Cron Jobs
- Agregar: `*/5 * * * * cd /home/usuario/public_html && python manage.py process_escalations`

### 9. Verificar funcionamiento
- Acceder a tu dominio
- Probar login en /admin/
- Verificar que los archivos estáticos se cargan correctamente

## Variables de entorno importantes

\`\`\`env
DEBUG=False
SECRET_KEY=clave-muy-segura-de-50-caracteres
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
DATABASE_URL=postgresql://usuario:pass@localhost:5432/bd_name
\`\`\`

## Solución de problemas comunes

### Error 500
- Revisar logs en `/logs/django.log`
- Verificar variables de entorno
- Comprobar permisos de archivos

### Archivos estáticos no cargan
- Ejecutar `python manage.py collectstatic --noinput`
- Verificar configuración de `.htaccess`

### Base de datos no conecta
- Verificar DATABASE_URL
- Comprobar que la BD existe en Hostinger
- Verificar credenciales
