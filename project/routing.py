from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from api import consumers

# The available url patterns for websocket connections
websocket_urlpatterns = [
    path('ws/matchmaking/', consumers.MatchmakingConsumer.as_asgi()),
    path('ws/trivia/<int:game_id>/', consumers.TriviaGameConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "websocket": URLRouter(websocket_urlpatterns),
})