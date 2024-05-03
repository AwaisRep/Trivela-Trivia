# Template

## Local development

To run this project in your development machine, follow these steps:

1. Create and activate a conda environment

2. Install Python dependencies (main folder):

    ```console
    $ pip install -r requirements.txt
    ```

4. Ensure postgres is installed and setup a database

5. Edit the django settings.py file to add the new database:

    ```console
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': '',  # Name of your database
            'USER': '',  # Database user
            'PASSWORD': '',  # Database password
            'HOST': '',  # Set to empty string for localhost
            'PORT': '',  # Set to empty string for default
        }
    }
    ```

6. Create a development database:

    ```console
    $ python manage.py migrate
    ```

7. Install JavaScript dependencies (from 'frontend' folder):

    ```console
    $ npm install
    ```

8. If everything is alright, you should be able to start the Django development server from the main folder:

    ```console
    $ python manage.py runserver
    ```

9. and the Vue server from the 'frontend' sub-folder:

    ```console
    $ npm run dev
    ```

10. Open your browser and go to http://localhost:5173, you will be greeted with the page.

NOTE: Make sure that the environment variables are set for the django secret key, if you intend to use for production. Otherwise use as such:
``` 
SECRET_KEY = os.getenv(
'DJANGO_SECRET_KEY',
# safe value used for development when DJANGO_SECRET_KEY might not be set
'' # Enter key here
)
```