import os
import django
import glob
import logging
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from api.models import DataLoadStatus

# Set up logging to output to stdout
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

if not DataLoadStatus.objects.exists(): # Make sure data has not been loaded before
    try:
        # Get a list of all JSON files in the bank_data directory
        json_files = sorted(glob.glob('bank_data/*.json'))

        # Run loaddata command for each file
        for file in json_files:
            os.system(f'python manage.py loaddata {file}')
            logging.info(f'Successfully loaded data from {file}')

        # Create a DataLoadStatus instance once finished
        DataLoadStatus.objects.create(data_loaded=True)
        logging.info('Successfully created DataLoadStatus instance')

    except Exception as e:
        logging.error(f'An error occurred: {e}')