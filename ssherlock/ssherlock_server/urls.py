"""All Django URLs for the SSHerlock server application."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("home", views.home, name="home"),
    path("add_credential", views.handle_credential, name="add_credential"),
    path("edit_credential/<uuid:uuid>", views.handle_credential, name="edit_credential"),

    #  path("add_target_host", views.add_target_host, name="add_target_host"),
    #  path("add_bastion_host", views.add_bastion_host, name="add_bastion_host"),
    #  path("add_llm_api", views.add_llm_api, name="add_llm_api"),
    #  path("create_job", views.create_job, name="create_job"),
    path("bastion_host", views.bastion_host_list, name="bastion_host_list"),
    path("credential", views.credential_list, name="credential_list"),
    path("job", views.job_list, name="job_list"),
    path("llm_api", views.llm_api_list, name="llm_api_list"),
    path("target_host", views.target_host_list, name="target_host_list"),
]
