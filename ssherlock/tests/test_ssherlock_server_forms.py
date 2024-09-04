from django.test import TestCase
from ssherlock_server.forms import (
    CredentialForm,
    BastionHostForm,
    TargetHostForm,
    LlmApiForm,
    JobForm,
)
from ssherlock_server.models import User, Credential, BastionHost, TargetHost, LlmApi


class TestCredentialForm(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="testuser@example.com")

    def test_valid_credential_form(self):
        form_data = {
            "credential_name": "Admin",
            "user": self.user.id,
            "username": "admin",
            "password": "supersecurepassword",
        }
        form = CredentialForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_credential_form_blank_credential_name(self):
        form_data = {
            "credential_name": "",
            "user": self.user.id,
            "username": "admin",
            "password": "supersecurepassword",
        }
        form = CredentialForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_credential_form_blank_user(self):
        form_data = {
            "credential_name": "Admin",
            "user": "",
            "username": "admin",
            "password": "supersecurepassword",
        }
        form = CredentialForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_credential_form_blank_username(self):
        form_data = {
            "credential_name": "Admin",
            "user": self.user.id,
            "username": "",
            "password": "supersecurepassword",
        }
        form = CredentialForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_credential_form_blank_password(self):
        form_data = {
            "credential_name": "Admin",
            "user": self.user.id,
            "username": "admin",
            "password": "",
        }
        form = CredentialForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_credential_form_name_too_long(self):
        field = "a" * 256
        form_data = {
            "credential_name": field,
            "user": self.user.id,
            "username": "admin",
            "password": "password",
        }
        form = CredentialForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_credential_form_username_too_long(self):
        field = "a" * 256
        form_data = {
            "credential_name": "Admin",
            "user": self.user.id,
            "username": field,
            "password": "password",
        }
        form = CredentialForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_credential_form_password_too_long(self):
        field = "a" * 256
        form_data = {
            "credential_name": "Admin",
            "user": self.user.id,
            "username": "username",
            "password": field,
        }
        form = CredentialForm(data=form_data)
        self.assertFalse(form.is_valid())


class TestBastionHostForm(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="testuser@example.com")

    def test_valid_bastion_host_form(self):
        form_data = {
            "hostname": "bastion.example.com",
            "user": self.user.id,
            "port": 22,
        }
        form = BastionHostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_bastion_host_form_blank_hostname(self):
        form_data = {
            "hostname": "",
            "user": self.user.id,
            "port": 22,
        }
        form = BastionHostForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_bastion_host_form_blank_user(self):
        form_data = {
            "hostname": "bastion.example.com",
            "user": "",
            "port": 22,
        }
        form = BastionHostForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_bastion_host_form_blank_port(self):
        form_data = {
            "hostname": "bastion.example.com",
            "user": self.user.id,
            "port": "",
        }
        form = BastionHostForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_bastion_host_form_hostname_too_long(self):
        field = "a" * 256
        form_data = {
            "hostname": field,
            "user": self.user.id,
            "port": 22,
        }
        form = BastionHostForm(data=form_data)
        self.assertFalse(form.is_valid())


class TestTargetHostForm(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="testuser@example.com")

    def test_valid_target_host_form(self):
        form_data = {
            "hostname": "target.example.com",
            "user": self.user.id,
            "port": 22,
        }
        form = TargetHostForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_target_host_form_blank_hostname(self):
        form_data = {
            "hostname": "",
            "user": self.user.id,
            "port": 22,
        }
        form = TargetHostForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_target_host_form_blank_user(self):
        form_data = {
            "hostname": "target.example.com",
            "user": "",
            "port": 22,
        }
        form = TargetHostForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_target_host_form_blank_port(self):
        form_data = {
            "hostname": "target.example.com",
            "user": self.user.id,
            "port": "",
        }
        form = TargetHostForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_target_host_form_hostname_too_long(self):
        field = "a" * 256
        form_data = {
            "hostname": field,
            "user": self.user.id,
            "port": 22,
        }
        form = TargetHostForm(data=form_data)
        self.assertFalse(form.is_valid())


class TestLlmApiForm(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="testuser@example.com")

    def test_valid_llm_api_form(self):
        form_data = {
            "base_url": "https://api.example.com",
            "api_key": "supersecretapikey",
            "user": self.user.id,
        }
        form = LlmApiForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_llm_api_form_blank_base_url(self):
        form_data = {
            "base_url": "",
            "api_key": "supersecretapikey",
            "user": self.user.id,
        }
        form = LlmApiForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_llm_api_form_blank_api_key(self):
        form_data = {
            "base_url": "https://api.example.com",
            "api_key": "",
            "user": self.user.id,
        }
        form = LlmApiForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_llm_api_form_blank_user(self):
        form_data = {
            "base_url": "https://api.example.com",
            "api_key": "supersecretapikey",
            "user": "",
        }
        form = LlmApiForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_llm_api_form_base_url_too_long(self):
        field = "https://" + "a" * 255 + ".com"
        form_data = {
            "base_url": field,
            "api_key": "supersecretapikey",
            "user": self.user.id,
        }
        form = LlmApiForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_llm_api_form_api_key_too_long(self):
        field = "a" * 256
        form_data = {
            "base_url": "https://api.example.com",
            "api_key": field,
            "user": self.user.id,
        }
        form = LlmApiForm(data=form_data)
        self.assertFalse(form.is_valid())


class TestJobForm(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="testuser@example.com")
        self.credential = Credential.objects.create(credential_name="Test", username="Admin", password="password", user=self.user)
        self.llm_api = LlmApi.objects.create(
            base_url="https://api.example.com", api_key="apikey", user=self.user
        )
        self.bastion_host = BastionHost.objects.create(
            hostname="bastion.example.com", user=self.user, port=22
        )
        self.target_host1 = TargetHost.objects.create(
            hostname="target1.example.com", user=self.user, port=22
        )
        self.target_host2 = TargetHost.objects.create(
            hostname="target2.example.com", user=self.user, port=22
        )

    def test_valid_job_form_blank_bastion_host(self):
        form_data = {
            "llm_api": self.llm_api.id,
            "bastion_host": None,
            "credentials_for_bastion_host": self.credential,
            "target_hosts": [self.target_host1, self.target_host2],
            "credentials_for_target_hosts": self.credential,
            "instructions": "Do something",
            "user": self.user.id,
        }
        form = JobForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_valid_job_form_blank_credential_for_bastion_host(self):
        form_data = {
            "llm_api": self.llm_api.id,
            "bastion_host": self.bastion_host,
            "credentials_for_bastion_host": None,
            "target_hosts": [self.target_host1, self.target_host2],
            "credentials_for_target_hosts": self.credential,
            "instructions": "Do something",
            "user": self.user.id,
        }
        form = JobForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_job_form_blank_llm_api(self):
        form_data = {
            "llm_api": None,
            "bastion_host": self.bastion_host,
            "credentials_for_bastion_host": None,
            "target_hosts": [self.target_host1, self.target_host2],
            "credentials_for_target_hosts": self.credential,
            "instructions": "Do something",
            "user": self.user.id,
        }
        form = JobForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_job_form_blank_target_hosts(self):
        form_data = {
            "llm_api": self.llm_api,
            "bastion_host": None,
            "credentials_for_bastion_host": None,
            "target_hosts": None,
            "credentials_for_target_hosts": self.credential,
            "instructions": "Do something",
            "user": self.user.id,
        }
        form = JobForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_job_form_blank_instructions(self):
        form_data = {
            "llm_api": self.llm_api,
            "bastion_host": None,
            "credentials_for_bastion_host": None,
            "target_hosts": [self.target_host1, self.target_host2],
            "credentials_for_target_hosts": self.credential,
            "instructions": "",
            "user": self.user.id,
        }
        form = JobForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_job_form_instructions_too_long(self):
        field = "a" * 128001
        form_data = {
            "llm_api": self.llm_api,
            "bastion_host": None,
            "credentials_for_bastion_host": None,
            "target_hosts": [self.target_host1, self.target_host2],
            "credentials_for_target_hosts": self.credential,
            "instructions": field,
            "user": self.user.id,
        }
        form = JobForm(data=form_data)
        self.assertFalse(form.is_valid())
