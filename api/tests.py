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

    def test_login(self):
        ''' Test to ensure a user can login '''
        response = self.client.post(reverse('login'), {
            'email': 'test@test03.com',
            'password': 'Test2003'
        })

        # Check that the response has a status code of 302 (redirect)
        self.assertEqual(response.status_code, 302)

        # Check that the user is authenticated
        user = get_user_model().objects.get(email='test@test03.com')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_logout(self):
        ''' Test to ensure a user can logout '''
        # Log the user in
        self.client.login(email='test@test03.com', password='Test2003')

        # Log the user out
        response = self.client.post(reverse('logout'))  # Change this line

        # Check that the response has a status code of 302 (redirect)
        self.assertEqual(response.status_code, 302)

        # Check that the user is not authenticated
        self.assertNotIn('_auth_user_id', self.client.session)