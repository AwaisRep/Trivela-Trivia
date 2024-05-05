# Template

## Local development

To run this project in your development machine, follow these steps:

1. Create and activate a conda environment

2. CD into the folder where the project is stored

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

    For safer practice, I advise using environment variables to store this data in the following manner:
    ```
    DB_HOST
    DB_NAME
    DB_PASSWORD
    DB_PORT
    DB_USER
    ```

6. Setup up the environment keys for upholding the initial session

    ```
    SUPERUSER_EMAIL
    SUPERUSER_PASSWORD
    SUPERUSER_USERNAME
    SUPERUSER_URL: url that will hold the endpoint for the admin panel (only accessible on the django port, which is usually 8000)
    ```

6. Create a development database:

    ```console
    $ python manage.py makemigrations
    $ python manage.py migrate
    ```

7. Load the initial data for the games:

    ```
    $ python load_initial_data.py
    ```

7. Install JavaScript dependencies (from 'frontend' folder):

    ```console
    $ cd frontend
    $ npm install
    ```

8. If everything has succeeded, you should be able to start the Django development server from the main folder:

    ```console
    $ daphne -b 0.0.0.0 -p 8000 project.asgi:application
    ```

9. and the Vue server from the 'frontend' sub-folder:

    ```console
    $ npm run dev
    ```

    I suggest opening two conda consoles (activating the environment twice) and then starting both servers

10. Open your browser and go to http://localhost:5173, you will be greeted with the page.

NOTE: Make sure that the environment variables are set for the django secret key, if you intend to use for production. Otherwise use as such:
``` 
SECRET_KEY = os.getenv(
'DJANGO_SECRET_KEY',
# safe value used for development when DJANGO_SECRET_KEY might not be set
'' # Enter key here
)
```