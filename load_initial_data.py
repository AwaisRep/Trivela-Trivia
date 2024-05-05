import os
import django
import glob

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from api.models import DataLoadStatus

if not DataLoadStatus.objects.exists(): # Make sure data has not been loaded before
    try:
        # Get a list of all JSON files in the bank_data directory
        json_files = glob.glob('bank_data/*.json')

        # Run loaddata command for each file
        for file in json_files:
            os.system(f'python manage.py loaddata {file}')
            print(f'Successfully loaded data from {file}')

        # Create a DataLoadStatus instance once finished to prevent from occuring again
        DataLoadStatus.objects.create(data_loaded=True)
        print('Successfully created DataLoadStatus instance')

    except Exception as e:
        print(f'An error occurred: {e}')