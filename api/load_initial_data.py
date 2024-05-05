import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from api.models import DataLoadStatus

if not DataLoadStatus.objects.exists(): # Make sure data has not been loaded before
    # Run loaddata command
    os.system('python manage.py loaddata data.json')
    # Create a DataLoadStatus instance once finished
    DataLoadStatus.objects.create(data_loaded=True)