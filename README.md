# Helpdesk v3.01

Sistema de gestión de tickets de soporte con internacionalización (i18n) en español e inglés.

## 🌍 Internacionalización (i18n)

Este proyecto soporta múltiples idiomas mediante el sistema de internacionalización de Django.

### Idiomas Soportados

- 🇪🇸 **Español (es)** - Idioma predeterminado
- 🇬🇧 **English (en)** - Inglés

### Funcionalidades i18n

#### Auto-detección de idioma

El sistema detecta automáticamente el idioma del navegador del usuario y establece la interfaz en ese idioma. Si el navegador está configurado en español o inglés, la plataforma se mostrará en ese idioma automáticamente.

#### Cambio manual de idioma

Los usuarios pueden cambiar manualmente el idioma usando el selector de idioma en la barra de navegación:

1. Haz clic en el ícono del globo (🌐) en la barra de navegación
2. Selecciona tu idioma preferido (Español o English)
3. La página se recargará con el nuevo idioma

### Configuración Técnica

#### Configuración en `settings.py`

```python
# Idioma predeterminado
LANGUAGE_CODE = 'es'

# Idiomas soportados
LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
]

# Ubicación de archivos de traducción
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Activar internacionalización
USE_I18N = True
```

#### Middleware

El `LocaleMiddleware` está configurado para detectar y establecer el idioma del usuario:

```python
MIDDLEWARE = [
    ...
    'django.middleware.locale.LocaleMiddleware',
    ...
]
```

#### URLs

El endpoint `/i18n/setlang/` está disponible para cambios manuales de idioma a través de formularios POST.

### Cómo Agregar Nuevas Traducciones

#### 1. Marcar cadenas para traducción

En **templates**, usa las etiquetas de traducción:

```django
{% load i18n %}

{# Para texto simple #}
<h1>{% trans "Bienvenido" %}</h1>

{# Para texto con variables #}
{% blocktrans %}
Hola {{ user_name }}, tienes {{ count }} tickets pendientes.
{% endblocktrans %}
```

En **código Python** (views, models, forms):

```python
from django.utils.translation import gettext_lazy as _

class TicketModel(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name=_("Título")
    )
```

#### 2. Generar archivos de mensajes

Ejecuta el comando para extraer todas las cadenas marcadas para traducción:

```bash
python manage.py makemessages -l es -l en --ignore=venv --ignore=env
```

Este comando:
- Busca todas las cadenas marcadas con `{% trans %}`, `{% blocktrans %}`, `_()`, o `gettext_lazy()`
- Genera/actualiza archivos `.po` en `locale/es/LC_MESSAGES/` y `locale/en/LC_MESSAGES/`

#### 3. Editar traducciones

Abre los archivos `.po` generados y agrega las traducciones:

**locale/es/LC_MESSAGES/django.po:**
```
msgid "Welcome"
msgstr "Bienvenido"
```

**locale/en/LC_MESSAGES/django.po:**
```
msgid "Bienvenido"
msgstr "Welcome"
```

#### 4. Compilar mensajes

Después de editar las traducciones, compila los archivos `.po` a `.mo`:

```bash
python manage.py compilemessages
```

#### 5. Verificar cambios

Reinicia el servidor de desarrollo y verifica que las traducciones aparezcan correctamente:

```bash
python manage.py runserver
```

### Agregar un Nuevo Idioma

Para agregar soporte para un nuevo idioma (por ejemplo, francés):

1. **Actualizar `settings.py`:**
```python
LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
    ('fr', 'Français'),  # Nuevo idioma
]
```

2. **Generar archivos de mensajes:**
```bash
python manage.py makemessages -l fr
```

3. **Traducir el archivo `.po` generado:**
```bash
# Editar locale/fr/LC_MESSAGES/django.po
```

4. **Compilar mensajes:**
```bash
python manage.py compilemessages
```

5. **Actualizar el selector de idioma en `templates/base.html`:**
```html
<button type='submit' name='language' value='fr' class='...'>
  <span class='text-lg'>🇫🇷</span>
  <span>Français</span>
</button>
```

### Estructura de Archivos de Traducción

```
helpdeskv3/
├── locale/
│   ├── es/
│   │   └── LC_MESSAGES/
│   │       ├── django.po    # Archivo de traducción editable
│   │       └── django.mo    # Archivo compilado (generado automáticamente)
│   └── en/
│       └── LC_MESSAGES/
│           ├── django.po
│           └── django.mo
```

### Mejores Prácticas

1. **Siempre marca las cadenas desde el principio:** Es más fácil marcar las cadenas para traducción cuando escribes el código que agregar traducciones después.

2. **Usa contextos para cadenas ambiguas:** Si una palabra puede significar cosas diferentes en diferentes contextos, usa el argumento `context`:
```python
from django.utils.translation import pgettext_lazy

pgettext_lazy("menu item", "File")  # Archivo (menú)
pgettext_lazy("document", "File")   # Archivo (documento)
```

3. **No concatenes cadenas traducidas:** En lugar de concatenar, usa variables:
```django
{# ❌ Mal #}
{% trans "Hola" %} {{ user_name }}

{# ✅ Bien #}
{% blocktrans %}Hola {{ user_name }}{% endblocktrans %}
```

4. **Mantén las traducciones actualizadas:** Ejecuta `makemessages` regularmente después de agregar nuevas características.

5. **Prueba en todos los idiomas:** Verifica que la interfaz se vea correctamente en todos los idiomas soportados.

### Herramientas Recomendadas

- **Poedit:** Editor gráfico para archivos `.po` (https://poedit.net/)
- **Django Rosetta:** Interfaz web para gestionar traducciones (opcional)

### Testing

El proyecto incluye tests automatizados para verificar la funcionalidad i18n:

```bash
# Ejecutar todos los tests de i18n
python manage.py test apps.tickets.test_i18n

# Ejecutar tests con más detalle
python manage.py test apps.tickets.test_i18n --verbosity=2
```

Los tests verifican:
- Configuración correcta de i18n en settings
- Presencia de LocaleMiddleware
- Existencia de archivos de traducción compilados
- Funcionamiento de traducciones en español e inglés
- Traducciones en modelos de Django

### Soporte

Para preguntas o problemas relacionados con traducciones, contacta al equipo de desarrollo.

---

## 🚀 Instalación y Configuración

### Requisitos Previos

- Python 3.8+
- Django 4.x
- PostgreSQL (producción) o SQLite (desarrollo)
- Redis (para Celery y Channels en producción)
- GNU gettext tools (para generar traducciones)

### Instalación

1. **Clonar el repositorio:**
```bash
git clone https://github.com/Jhoelperaltap/helpdeskv3.git
cd helpdeskv3
```

2. **Crear entorno virtual:**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Instalar gettext (para traducciones):**

En Ubuntu/Debian:
```bash
sudo apt-get install gettext
```

En macOS:
```bash
brew install gettext
```

En Windows:
- Descargar desde https://mlocati.github.io/articles/gettext-iconv-windows.html

5. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

6. **Ejecutar migraciones:**
```bash
python manage.py migrate
```

7. **Compilar traducciones:**
```bash
python manage.py compilemessages
```

8. **Crear superusuario:**
```bash
python manage.py createsuperuser
```

9. **Ejecutar servidor de desarrollo:**
```bash
python manage.py runserver
```

### Ejecutar Tests

```bash
# Ejecutar todos los tests
python manage.py test

# Ejecutar tests de i18n específicamente
python manage.py test apps.tickets.test_i18n
```

## 📱 Características

- ✅ Sistema de tickets multiempresa
- ✅ Roles de usuario (Cliente, Agente, Administrador, Superadmin)
- ✅ Asignación automática y manual de tickets
- ✅ Sistema de escalamiento automático
- ✅ Notificaciones en tiempo real (WebSocket)
- ✅ **Internacionalización (Español/Inglés)**
- ✅ Dashboard con métricas
- ✅ Filtros avanzados de tickets
- ✅ Adjuntos de archivos
- ✅ Historial de mensajes

## 🌐 Idiomas

- 🇪🇸 Español (predeterminado)
- 🇬🇧 English

El sistema detecta automáticamente el idioma del navegador y los usuarios pueden cambiarlo manualmente desde la interfaz.

## Soporte
