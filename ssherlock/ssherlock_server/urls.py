from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing_page"),
    path("home", views.home, name="home_page"),
    path("target_servers", views.target_servers, name="target_servers"),
]
