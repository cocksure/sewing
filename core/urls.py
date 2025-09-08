from django.urls import path

from core import views

urlpatterns = [
    path('settings/', views.settings, name='settings'),
]
