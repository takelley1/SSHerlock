from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("home", views.home, name="home"),
    path("add_credential", views.add_credential, name="add_credential"),
    #  path("add_target_server", views.add_target_server, name="add_target_server"),
    #  path("add_bastion_server", views.add_bastion_server, name="add_bastion_server"),
    #  path("add_llm_api", views.add_llm_api, name="add_llm_api"),
    #  path("create_job", views.create_job, name="create_job"),
    path("bastion_server", views.bastion_server_list, name="bastion_server_list"),
    path("credential", views.credential_list, name="credential_list"),
    path("job", views.job_list, name="job_list"),
    path("llm_api", views.llm_api_list, name="llm_api_list"),
    path("target_server", views.target_server_list, name="target_server_list"),
]
