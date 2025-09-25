#!/usr/bin/env python
"""
Run tests with coverage reporting
"""
import os
import sys
import subprocess

def run_coverage():
    """Run tests with coverage analysis"""
    
    # Install coverage if not available
    try:
        import coverage
    except ImportError:
        print("Installing coverage...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'coverage'])
        import coverage
    
    # Initialize coverage
    cov = coverage.Coverage(
        source=['apps'],
        omit=[
            '*/migrations/*',
            '*/tests/*',
            '*/venv/*',
            '*/env/*',
            'manage.py',
            'config/wsgi.py',
            'config/asgi.py',
        ]
    )
    
    cov.start()
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_settings')
    import django
    django.setup()
    
    # Run tests
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=False)
    failures = test_runner.run_tests(['tests'])
    
    # Stop coverage and generate report
    cov.stop()
    cov.save()
    
    print("\n" + "="*50)
    print("COVERAGE REPORT")
    print("="*50)
    cov.report()
    
    # Generate HTML report
    cov.html_report(directory='htmlcov')
    print(f"\nHTML coverage report generated in 'htmlcov' directory")
    
    if failures:
        sys.exit(1)

if __name__ == '__main__':
    run_coverage()
