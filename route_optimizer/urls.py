from django.urls import path

from .views import health_view, route_api

urlpatterns = [
    path('health/', health_view, name='health'),
    path('route/', route_api, name='route-api'),
]
