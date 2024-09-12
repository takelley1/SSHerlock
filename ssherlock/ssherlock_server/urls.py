"""All Django URLs for the SSHerlock server application."""

# pylint: disable=import-error
from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("home", views.home, name="home"),
    path("add/job", views.create_job, name="create_job"),
    path("add/<str:model_type>", views.handle_object, name="add_object"),
    path("edit/<str:model_type>/<uuid:uuid>", views.handle_object, name="edit_object"),
    path(
        "delete/<str:model_type>/<uuid:uuid>", views.delete_object, name="delete_object"
    ),
    path("bastion_host_list", views.bastion_host_list, name="bastion_host_list"),
    path("credential_list", views.credential_list, name="credential_list"),
    path("job_list", views.job_list, name="job_list"),
    path("llm_api_list", views.llm_api_list, name="llm_api_list"),
    path("target_host_list", views.target_host_list, name="target_host_list"),
    path("request_job", views.request_job, name="request_job"),
    path(
        "update_job_status/<uuid:job_id>/", views.update_job_status, name="update_job_status"
    ),
    path(
        "get_job_status/<uuid:job_id>/", views.get_job_status, name="get_job_status"
    ),
]
