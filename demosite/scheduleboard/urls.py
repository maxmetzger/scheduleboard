from django.urls import path

from . import views
"""
The schedule board has two paths: a default path that lets the view pick the default station, and a /station URL that
includes the user's selected station.
"""

urlpatterns = [
    path('', views.index, name='index'),
    path('station', views.index, name='index')
]
