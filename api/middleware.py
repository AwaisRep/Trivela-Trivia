from django.http import HttpResponseRedirect
from django.conf import settings  # Importing settings so we can import the frontend environment variable

class ErrorHandlingMiddleware:
    ''' This class is designed to redirect any url's that are not found or are forbidden to unauthenticated users '''
    def __init__(self, get_response):
        self.get_response = get_response # Retrieve the initial response

    def __call__(self, request):
        response = self.get_response(request)
        # Check if the request path is not already the landing, login or sign up page
        if request.path not in ['/landing', '/login', '/signup']:
            if response.status_code == 404 and request.user.is_authenticated:
                return HttpResponseRedirect(settings.FRONTEND_URL + '/landing')  # Redirect to landing page if the page does not exist
            elif response.status_code == 403 and request.user.is_authenticated:
                return HttpResponseRedirect(settings.FRONTEND_URL + '/landing')  # Redirect to landing page if they are not logged in
        return response