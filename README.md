# Template

## Local development

To run this project in your development machine, follow these steps:

1. Create and activate a conda environment
    ```console
    $ conda create -n <name>
    $ conda activate <name>
    ```

2. CD into the folder where the project is stored
    ```console
    $ cd <path_to_project>
    ```

3. Install Python dependencies (main folder):

    ```console
    $ pip install -r requirements.txt
    ```

4. Ensure postgres is installed and setup a database

5. Edit the django settings.py file to add the new database:

    ```
    *Edit the second value, if you don't intend to use environment variables*
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', ''),  # Name of your database
            'USER': os.environ.get('DB_USER', ''),  # Database user
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),  # Database password
            'HOST': os.environ.get('DB_HOST', ''),  # Set to empty string for localhost
            'PORT': os.environ.get('DB_PORT', '5432'),  # Set to empty string for default
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

6. Setup up the environment keys for upholding the initial superuser

    ```
    SUPERUSER_EMAIL
    SUPERUSER_PASSWORD
    SUPERUSER_USERNAME
    SUPERUSER_URL: url that will hold the endpoint for the admin panel (only accessible on the django port in dev, which is usually 8000)
    ```

    If you don't intend to use environment variables, then these values will hold the admin user:
    ```
    username = admin
    email = admin@triveltrivia.com
    password = Admin1234
    admin_url = admin/ # Endpoint to access the admin panel on the django port
    ```

7. Allow the superuser to be created

   ```console
   $ python create_superuser.py
   ```

   The admin panel will be available based on the environment variable you set in step 

8. Create a development database:

    ```console
    $ python manage.py makemigrations
    $ python manage.py migrate
    ```

9. Load the initial data for the games:

    ```console
    $ python load_initial_data.py
    ```

10. Install JavaScript dependencies (from 'frontend' folder):

    ```console
    $ cd frontend
    $ npm install
    ```

11. If everything has succeeded, you should be able to start the Django development server from the main folder:

    ```console
    $ daphne -b 0.0.0.0 -p 8000 project.asgi:application
    ```

12. and the Vue server from the 'frontend' sub-folder:

    ```console
    $ npm run dev
    ```

    I suggest opening two conda consoles (activating the environment twice) and then starting both servers

13. Open your browser and go to http://localhost:5173, you will be greeted with the page.


NOTE: Make sure that the environment variables are set for the django secret key, if you intend to use for production. Otherwise it will use the default value as such:
``` 
SECRET_KEY = os.getenv(
'DJANGO_SECRET_KEY',
# safe value used for development when DJANGO_SECRET_KEY might not be set
'default_secret_key_for_development_only' # Enter key here
)
```

Here are how you can set environment keys from your command line:

```
Windows: setx KEY "VALUE"
Unix-based systems: $ export KEY=VALUE
```