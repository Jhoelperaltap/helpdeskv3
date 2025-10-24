"""
Tests for internationalization (i18n) functionality
"""
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import translation


class InternationalizationTestCase(TestCase):
    """Test i18n configuration and language switching"""
    
    def setUp(self):
        self.client = Client()
    
    def test_i18n_settings_configured(self):
        """Test that i18n settings are properly configured"""
        from django.conf import settings
        
        # Check that i18n is enabled
        self.assertTrue(settings.USE_I18N)
        
        # Check that LANGUAGES is configured
        self.assertIn(('es', 'Español'), settings.LANGUAGES)
        self.assertIn(('en', 'English'), settings.LANGUAGES)
        
        # Check that LOCALE_PATHS is configured
        self.assertTrue(len(settings.LOCALE_PATHS) > 0)
    
    def test_middleware_configured(self):
        """Test that LocaleMiddleware is in MIDDLEWARE"""
        from django.conf import settings
        
        self.assertIn('django.middleware.locale.LocaleMiddleware', settings.MIDDLEWARE)
    
    def test_default_language_is_spanish(self):
        """Test that the default language is Spanish"""
        from django.conf import settings
        
        self.assertEqual(settings.LANGUAGE_CODE, 'es')
    
    def test_language_switching_url_exists(self):
        """Test that the language switching URL is configured"""
        from django.urls.exceptions import NoReverseMatch
        
        try:
            url = reverse('set_language')
            self.assertIsNotNone(url)
            self.assertTrue(url.startswith('/i18n/'))
        except NoReverseMatch:
            self.fail("Language switching URL 'set_language' not found in URL configuration")
    
    @override_settings(LANGUAGE_CODE='es')
    def test_spanish_translation(self):
        """Test that Spanish translations work"""
        with translation.override('es'):
            from django.utils.translation import gettext as _
            
            # Test translations from English msgids
            self.assertEqual(_('Dashboard'), 'Panel de Control')
            self.assertEqual(_('Tickets'), 'Tickets')
    
    @override_settings(LANGUAGE_CODE='en')
    def test_english_translation(self):
        """Test that English translations work"""
        with translation.override('en'):
            from django.utils.translation import gettext as _
            
            # Test translations from Spanish msgids to English
            self.assertEqual(_('Notificaciones'), 'Notifications')
            self.assertEqual(_('Administración'), 'Administration')
    
    def test_ticket_model_translations(self):
        """Test that Ticket model has translatable fields"""
        from apps.tickets.models import Ticket
        from django.utils.translation import gettext_lazy as _
        
        # Check that STATUS choices are translatable
        status_values = [choice[0] for choice in Ticket.STATUS]
        self.assertIn('OPEN', status_values)
        self.assertIn('IN_PROGRESS', status_values)
        self.assertIn('RESOLVED', status_values)
        self.assertIn('CLOSED', status_values)
        
        # Check that PRIORITY choices are translatable
        priority_values = [choice[0] for choice in Ticket.PRIORITY]
        self.assertIn('LOW', priority_values)
        self.assertIn('MEDIUM', priority_values)
        self.assertIn('HIGH', priority_values)
    
    def test_compiled_message_files_exist(self):
        """Test that compiled message files exist"""
        import os
        from django.conf import settings
        
        locale_path = settings.LOCALE_PATHS[0]
        
        # Check Spanish .mo file
        es_mo_path = os.path.join(locale_path, 'es', 'LC_MESSAGES', 'django.mo')
        self.assertTrue(os.path.exists(es_mo_path), f"Spanish .mo file not found at {es_mo_path}")
        
        # Check English .mo file
        en_mo_path = os.path.join(locale_path, 'en', 'LC_MESSAGES', 'django.mo')
        self.assertTrue(os.path.exists(en_mo_path), f"English .mo file not found at {en_mo_path}")
