"""
ASGI config for the project.
It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.urls import path
from api.consumers import MatchmakingConsumer, TriviaGameConsumer

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack( # This sets the websocket middleware urls
        URLRouter([
            path('ws/matchmaking/', MatchmakingConsumer.as_asgi()),
            path('ws/trivia/<int:game_id>/', TriviaGameConsumer.as_asgi()),
        ])
    ),
})
