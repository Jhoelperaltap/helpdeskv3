from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import logout
from django.contrib import messages
from django.conf import settings
import time

class SessionTimeoutMiddleware:
    """
    Middleware to handle automatic session timeout due to inactivity
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip timeout check for certain URLs
        skip_urls = [
            reverse('users:login'),
            reverse('users:logout'),
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        # Check if current path should be skipped
        skip_timeout = any(request.path.startswith(url) for url in skip_urls)
        
        if request.user.is_authenticated and not skip_timeout:
            # Get current time
            now = time.time()
            
            # Get last activity from session
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                # Calculate time since last activity
                time_since_activity = now - last_activity
                
                # Check if session has expired
                if time_since_activity > settings.SESSION_COOKIE_AGE:
                    # Log out user and redirect to login
                    logout(request)
                    messages.warning(request, 'Tu sesión ha expirado por inactividad. Por favor, inicia sesión nuevamente.')
                    return redirect('users:login')
            
            # Update last activity time
            request.session['last_activity'] = now
            
            # Add session info to request for JavaScript
            request.session_expires_at = now + settings.SESSION_COOKIE_AGE
            request.session_warning_at = now + settings.SESSION_COOKIE_AGE - getattr(settings, 'SESSION_TIMEOUT_WARNING', 300)

        response = self.get_response(request)
        return response
