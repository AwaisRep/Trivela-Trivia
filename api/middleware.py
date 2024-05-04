from django.shortcuts import redirect
from django.http import HttpResponseNotFound, HttpResponseForbidden

class ErrorHandlingMiddleware:
    ''' This class is designed to redirect any url's that are not found or are forbidden to unauthenticated users '''
    def __init__(self, get_response):
        self.get_response = get_response # Retrieve the initial response

    def __call__(self, request):
        response = self.get_response(request)
        if isinstance(response, HttpResponseNotFound) and request.user.is_authenticated:
            return redirect('landing')  # Redirect to landing page if the page does not exist
        elif isinstance(response, HttpResponseForbidden) and request.user.is_authenticated:
            return redirect('landing')  # Redirect to landing page if they are not logged in
        return response