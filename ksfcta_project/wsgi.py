"""
WSGI config for ksfcta_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import shutil
from pathlib import Path
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ksfcta_project.settings')

# Ensure /tmp/db.sqlite3 exists and is writable on Vercel Serverless
if os.environ.get('VERCEL'):
    try:
        from django.conf import settings
        tmp_db = Path('/tmp/db.sqlite3')
        orig_db = settings.BASE_DIR / 'db.sqlite3'
        if not tmp_db.exists() and orig_db.exists():
            shutil.copyfile(orig_db, tmp_db)
    except Exception as e:
        print("DB copy error:", e)

application = get_wsgi_application()
app = application

# Self-healing on Vercel: run migrations and ensure admin 'shafi' exists
if os.environ.get('VERCEL'):
    try:
        from django.core.management import call_command
        from django.contrib.auth.models import User
        call_command('migrate', interactive=False)
        admin_user = User.objects.filter(username='shafi').first()
        if not admin_user:
            User.objects.create_superuser('shafi', 'shafi@ksfcta.org', 'shafi@pulpara')
        else:
            admin_user.set_password('shafi@pulpara')
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.is_active = True
            admin_user.save()
    except Exception as e:
        print("Vercel startup init error:", e)

