# create_superuser.py
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

import django
django.setup()

from api.models import User  # Import the user so we can create a superuser based on the user model

# Basic superuser credentials if none are provided in the environment variables
username = os.getenv('SUPERUSER_USERNAME', 'admin')
email = os.getenv('SUPERUSER_EMAIL', 'admin@trivelatrivia.com')
password = os.getenv('SUPERUSER_PASSWORD', 'Admin1234')

if not User.objects.filter(username=username).exists(): # Gurantees we don't try an override execution
    User.objects.create_superuser(username, email, password)