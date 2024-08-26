"""All Django URLs for the SSHerlock server application."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("home", views.home, name="home"),
    path("add/<str:model_type>", views.handle_object, name="add_object"),
    path("edit/<str:model_type>/<uuid:uuid>", views.handle_object, name="edit_object"),
    path("bastion_host", views.bastion_host_list, name="bastion_host_list"),
    path("credential", views.credential_list, name="credential_list"),
    path("job", views.job_list, name="job_list"),
    path("llm_api", views.llm_api_list, name="llm_api_list"),
    path("target_host", views.target_host_list, name="target_host_list"),
]
