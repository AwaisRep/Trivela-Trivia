from django.conf import settings
from django.urls import include, path, re_path
from django.conf.urls.static import static
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter

from api import views
from .views import main_spa, UserProfileHistoryView, BoxToBoxView, CareerPathView, GuessTheSideView
app_name = 'api'

#Handles all the url's served by the rest framework
router = DefaultRouter()
router.register(r'check_auth', UserProfileHistoryView, basename='check_auth')
router.register(r'users', views.UserViewSet, basename='users')

urlpatterns = [
    path('', main_spa),
    path('', include(router.urls)),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.custom_logout, name='logout'),
    path('leaderboard', views.leaderboard, name='leaderboard'), #Endpoint for the leaderboard

    #Patterns:
    # _get_game -> Retrieve all games that can be played
    # _game -> Retrieve game data about a specific game
    # _guess -> Guess endpoint for a specific game in mind
    # session_id and game denote the same field, they are seperated for logic as there are two POST methods in each class

    path('box2box/game/', BoxToBoxView.as_view(), name='box2box_get_game'),
    path('box2box/game/<int:game_id>', BoxToBoxView.as_view(), name='box2box_game'),
    path('box2box/guess/<int:session_id>', BoxToBoxView.as_view(), name='box2box_guess'),

    path('career_path/game/', CareerPathView.as_view(), name='career_path_get_game'),
    path('career_path/game/<int:game_id>', CareerPathView.as_view(), name='career_path_game'),
    path('career_path/guess/<int:session_id>', CareerPathView.as_view(), name='career_path_guess'),

    path('guess_the_side/game/', GuessTheSideView.as_view(), name='gts_get_game'),
    path('guess_the_side/game/<int:game_id>', GuessTheSideView.as_view(), name='gts_game'),
    path('guess_the_side/guess/<int:session_id>', GuessTheSideView.as_view(), name='gts_guess'),

    re_path(r'^.*$', TemplateView.as_view(template_name='api/spa/index.html'), name='home'), # Ensure the user is redirected to the vue page if any other url is entered
    # We use a regex to match any other pattern that has not been defined above this
]


if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL,
                              document_root=settings.MEDIA_ROOT)
#Used in order to set the path for where static files are stored (vue files for instance)