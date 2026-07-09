from django.urls import path

from .views import health_view, index, route_api

urlpatterns = [
    path('', index, name='index'),
    path('health/', health_view, name='health'),
    path('route/', route_api, name='route-api'),
]
