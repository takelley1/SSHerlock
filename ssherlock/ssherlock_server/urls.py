"""All Django URLs for the SSHerlock server application."""

# pylint: disable=import-error
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView

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
    path("retry/job/<uuid:job_id>", views.retry_job, name="retry_job"),
    path("bastion_host_list", views.bastion_host_list, name="bastion_host_list"),
    path("credential_list", views.credential_list, name="credential_list"),
    path("job_list", views.job_list, name="job_list"),
    path("llm_api_list", views.llm_api_list, name="llm_api_list"),
    path("target_host_list", views.target_host_list, name="target_host_list"),
    path("request_job", views.request_job, name="request_job"),
    path(
        "update_job_status/<uuid:job_id>",
        views.update_job_status,
        name="update_job_status",
    ),
    path("get_job_status/<uuid:job_id>", views.get_job_status, name="get_job_status"),
    path("log_job_data/<uuid:job_id>", views.log_job_data, name="log_job_data"),
    path("view_job/<uuid:job_id>", views.view_job, name="view_job"),
    path("view_job/<uuid:job_id>/log", views.stream_job_log, name="stream_job_log"),
    path("cancel_job/<uuid:job_id>", views.cancel_job, name="cancel_job"),
    path("account/", views.account, name="account"),
    path("reset_password/", views.reset_password, name="reset_password"),
    path("accounts/login/", LoginView.as_view(template_name='login.html'), name="login"),
    path("accounts/logout/", LogoutView.as_view(next_page='/'), name="logout"),
    path("signup/", views.signup, name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),
]
