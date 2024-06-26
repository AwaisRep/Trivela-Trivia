from django.test import TestCase, Client
from django.urls import resolve, reverse
from django.contrib.auth import get_user_model
from .views import main_spa, login_view, signup_view, leaderboard

class URLTest(TestCase):
    ''' Test to ensure urls are correctly resolved '''

    def test_landing_page(self):
        ''' Make sure the landing page is resolved to unauthenticated users '''
        resolver = resolve('/') # Attempt to resolve the path '/
        self.assertEqual(resolver.func, main_spa) # Check that the function that is resolved is main_spa

    def test_login_page(self):
        ''' Make sure the login page is resolved '''
        resolver = resolve('/login/')
        self.assertEqual(resolver.func, login_view) # Check that the function that is resolved is login_view

    def test_signup_page(self):
        ''' Make sure the signup page is resolved '''
        resolver = resolve('/signup/')
        self.assertEqual(resolver.func, signup_view) # Check that the function that is resolved is signup_view

    def test_leaderboard_page(self):
        ''' Make sure the leaderboard page is resolved '''
        resolver = resolve('/leaderboard')
        self.assertEqual(resolver.func, leaderboard) # Check that the function that is resolved is leaderboard

class AuthenticationTest(TestCase):
    ''' Test to ensure authentication works correctly '''

    def test_signup(self):
        ''' Test to ensure a user can sign up '''
        form_data = {
            'email': 'foo@foobar.com',
            'username': 'rando09',
            'password1': 'Test2003',
            'password2': 'Test2003'
        } # Random form data that is unique

        response = self.client.post(reverse('api:signup'), form_data) # Access the route for view function signup
        self.assertEqual(response.status_code, 302)  # Successful redirect means that the user was signed up and redirected to the home page

    def test_login(self):
        ''' Test to ensure a user can login '''
        User = get_user_model()
        User.objects.create_user(username='awais03', email='test@test03.com', password='Test2003') # Create a random user (we don't need to worry about uniqueness)


        response = self.client.post(reverse('api:login'), {
            'email': 'test@test03.com',
            'password': 'Test2003'
        }) # Process the form data for the login view function

        self.assertEqual(response.status_code, 302) # Succesful redirect means that the user was logged in and redirected to the home page

    def test_logout(self):
        ''' Test to ensure a user can logout '''

        User = get_user_model()
        User.objects.create_user(username='awais03', email='test@test03.com', password='Test2003') # Create a user

        logged_in = self.client.login(username='test@test03.com', password='Test2003') # Log the user in
        self.assertTrue(logged_in)

        response = self.client.post(reverse('api:logout')) # Log the user out

        self.assertEqual(response.status_code, 302) # Check that the response has a status code of 302 (redirect)
        self.assertNotIn('_auth_user_id', self.client.session) # Check that the user is not authenticated in the session anymore