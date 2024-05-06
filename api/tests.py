from django.test import TestCase, Client
from django.urls import resolve, reverse
from django.contrib.auth import get_user_model
from .views import main_spa, login_view, signup_view, leaderboard

class URLTest(TestCase):
    ''' Test to ensure urls are correctly resolved '''

    def test_landing_page_resolves(self):
        ''' Make sure the landing page is resolved to unauthenticated users '''
        resolver = resolve('/')
        self.assertEqual(resolver.func, main_spa)

    def test_login_page_resolves(self):
        ''' Make sure the login page is resolved '''
        resolver = resolve('/login/')
        self.assertEqual(resolver.func, login_view)

    def test_signup_page_resolves(self):
        ''' Make sure the signup page is resolved '''
        resolver = resolve('/signup/')
        self.assertEqual(resolver.func, signup_view)

    def test_leaderboard_page_resolves(self):
        ''' Make sure the leaderboard page is resolved '''
        resolver = resolve('/leaderboard')
        self.assertEqual(resolver.func, leaderboard)

class AuthenticationTest(TestCase):
    ''' Test to ensure authentication works correctly '''

    def test_signup(self):
        ''' Test to ensure a user can sign up '''
        form_data = {
            'email': 'test@test03.com',
            'username': 'test03',
            'password': 'Test2003',
        }

        response = self.client.post(reverse('api:signup'), form_data)
        self.assertEqual(response.status_code, 302) # Succesful redirect means that the user was signed up and redirect to the home page

    def test_login(self):
        ''' Test to ensure a user can login '''
        User = get_user_model()
        User.objects.create_user(username='awais03', email='test@test03.com', password='Test2003')


        response = self.client.post(reverse('api:login'), {
            'email': 'test@test03.com',
            'password': 'Test2003'
        })

        self.assertEqual(response.status_code, 302) # Succesful redirect means that the user was logged in and redirected to the home page

    def test_logout(self):
        ''' Test to ensure a user can logout '''

        User = get_user_model()
        User.objects.create_user(username='awais03', email='test@test03.com', password='Test2003') # Create a user

        logged_in = self.client.login(username='test@test03.com', password='Test2003') # Log the user in
        self.assertTrue(logged_in)

        response = self.client.post(reverse('api:logout')) # Log the user out

        self.assertEqual(response.status_code, 302) # Check that the response has a status code of 302 (redirect)
        self.assertNotIn('_auth_user_id', self.client.session) # Check that the user is not authenticated