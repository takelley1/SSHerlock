"""Tests for all classes in views.py"""

# pylint: disable=import-error, missing-class-docstring, missing-function-docstring, invalid-str-returned, no-member, invalid-name

import uuid
import json
import os
from unittest.mock import patch, mock_open
from django.utils import timezone
from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.models import User
from ssherlock_server.models import (
    BastionHost,
    Credential,
    Job,
    LlmApi,
    TargetHost,
)

SSHERLOCK_SERVER_DOMAIN = "localhost:8000"
SSHERLOCK_SERVER_PROTOCOL = "http"
SSHERLOCK_SERVER_RUNNER_TOKEN = "myprivatekey"


class TestHandleObject(TestCase):
    """Tests for the handle_object view."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "testuser", "testuser@example.com", "password"
        )
        cls.bastion_host = BastionHost.objects.create(
            hostname="bastion-host.example.com", port=22, user=cls.user
        )
        cls.credential = Credential.objects.create(
            credential_name="my-credential",
            username="user",
            password="pass",
            user=cls.user,
        )
        cls.llm_api = LlmApi.objects.create(
            base_url="https://api.example.com", api_key="dummy_key", user=cls.user
        )
        cls.target_host = TargetHost.objects.create(
            hostname="target-host.example.com", port=22, user=cls.user
        )

    # #########################################################################
    # Generic functions.
    # #########################################################################

    def _GET_add_object(self, model_name):
        """Verify GET requests work to add objects."""
        response = self.client.get(reverse("add_object", args=[model_name]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "objects/add_object.html")

    def _GET_edit_object(self, model_name, iid):
        """Verify GET requests work to edit objects."""
        response = self.client.get(reverse("edit_object", args=[model_name, str(iid)]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "objects/edit_object.html")

    def _POST_add_object(self, model_name, new_object_str, data, expected_url):
        """Verify POSTS requests work to add objects."""
        response_add = self.client.post(reverse("add_object", args=[model_name]), data)
        self.assertEqual(response_add.status_code, 302)
        self.assertRedirects(response_add, expected_url)
        # Verify the newly-added object appears in the list of objects now.
        response_list = self.client.get(reverse(f"{model_name}_list"))
        self.assertContains(response_list, new_object_str)

    def _POST_edit_object(self, model_name, iid, edited_object_str, data, expected_url):
        """Verify POSTS requests work to edit objects."""
        response = self.client.post(
            reverse("edit_object", args=[model_name, str(iid)]), data
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url)
        # Verify the newly-edited object appears in the list of objects now.
        response_list = self.client.get(reverse(f"{model_name}_list"))
        self.assertContains(response_list, edited_object_str)

    # #########################################################################
    # Main test functions.
    # #########################################################################

    def test_bastion_host_add_authenticated(self):
        """Test adding a new bastion host while authenticated."""
        self.client.login(username="testuser", password="password")
        data = {
            "hostname": "new-bastion_host.example.com",
            "port": 22,
            "user": self.user.id,
        }
        self._GET_add_object("bastion_host")
        self._POST_add_object(
            "bastion_host", data["hostname"], data, "/bastion_host_list"
        )

    def test_bastion_host_add_not_authenticated(self):
        """Test adding a new bastion host while not authenticated redirects to login page."""
        data = {
            "hostname": "new-bastion_host.example.com",
            "port": 22,
            "user": self.user.id,
        }
        response = self.client.post(reverse("add_object", args=["bastion_host"]), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/add/bastion_host")

    def test_bastion_host_edit_authenticated(self):
        """Test editing an existing bastion host while authenticated."""
        self.client.login(username="testuser", password="password")
        data = {
            "hostname": "edited-bastion_host.example.com",
            "port": 22,
            "user": self.user.id,
        }
        self._GET_edit_object("bastion_host", self.bastion_host.id)
        self._POST_edit_object(
            "bastion_host",
            self.bastion_host.id,
            data["hostname"],
            data,
            "/bastion_host_list",
        )

    def test_bastion_host_edit_not_authenticated(self):
        """Test editing an existing bastion host while not authenticated redirects to login page."""
        data = {
            "hostname": "edited-bastion_host.example.com",
            "port": 22,
            "user": self.user.id,
        }
        response = self.client.post(
            reverse("edit_object", args=["bastion_host", str(self.bastion_host.id)]),
            data,
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f"/accounts/login/?next=/edit/bastion_host/{self.bastion_host.id}"
        )

    def test_target_host_add_authenticated(self):
        """Test adding a new target host while authenticated."""
        self.client.login(username="testuser", password="password")
        data = {
            "hostname": "new-target_host.example.com",
            "port": 22,
            "user": self.user.id,
        }
        self._GET_add_object("target_host")
        self._POST_add_object(
            "target_host", data["hostname"], data, "/target_host_list"
        )

    def test_target_host_add_not_authenticated(self):
        """Test adding a new target host while not authenticated redirects to login page."""
        data = {
            "hostname": "new-target_host.example.com",
            "port": 22,
            "user": self.user.id,
        }
        response = self.client.post(reverse("add_object", args=["target_host"]), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/add/target_host")

    def test_target_host_edit_authenticated(self):
        """Test editing an existing target host while authenticated."""
        self.client.login(username="testuser", password="password")
        data = {
            "hostname": "edited-target_host.example.com",
            "port": 22,
            "user": self.user.id,
        }
        self._GET_edit_object("target_host", self.target_host.id)
        self._POST_edit_object(
            "target_host",
            self.target_host.id,
            data["hostname"],
            data,
            "/target_host_list",
        )

    def test_target_host_edit_not_authenticated(self):
        """Test editing an existing target host while not authenticated redirects to login page."""
        data = {
            "hostname": "edited-target_host.example.com",
            "port": 22,
            "user": self.user.id,
        }
        response = self.client.post(
            reverse("edit_object", args=["target_host", str(self.target_host.id)]), data
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f"/accounts/login/?next=/edit/target_host/{self.target_host.id}"
        )

    def test_credential_add_authenticated(self):
        """Test adding a new credential while authenticated."""
        self.client.login(username="testuser", password="password")
        data = {
            "credential_name": "new-credential-name",
            "username": "new-credential-username",
            "password": "new-credential-password",
            "user": self.user.id,
        }
        self._GET_add_object("credential")
        self._POST_add_object(
            "credential", data["credential_name"], data, "/credential_list"
        )

    def test_credential_add_not_authenticated(self):
        """Test adding a new credential while not authenticated redirects to login page."""
        data = {
            "credential_name": "new-credential-name",
            "username": "new-credential-username",
            "password": "new-credential-password",
            "user": self.user.id,
        }
        response = self.client.post(reverse("add_object", args=["credential"]), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/add/credential")

    def test_credential_edit_authenticated(self):
        """Test editing an existing credential while authenticated."""
        self.client.login(username="testuser", password="password")
        data = {
            "credential_name": "edited-credential-name",
            "username": "edited-credential-username",
            "password": "edited-credential-password",
            "user": self.user.id,
        }
        self._GET_edit_object("credential", self.credential.id)
        self._POST_edit_object(
            "credential",
            self.credential.id,
            data["credential_name"],
            data,
            "/credential_list",
        )

    def test_credential_edit_not_authenticated(self):
        """Test editing an existing credential while not authenticated redirects to login page."""
        data = {
            "credential_name": "edited-credential-name",
            "username": "edited-credential-username",
            "password": "edited-credential-password",
            "user": self.user.id,
        }
        response = self.client.post(
            reverse("edit_object", args=["credential", str(self.credential.id)]), data
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f"/accounts/login/?next=/edit/credential/{self.credential.id}"
        )

    def test_llm_api_add_authenticated(self):
        """Test adding a new LLM API while authenticated."""
        self.client.login(username="testuser", password="password")
        data = {
            "base_url": "new-llmapi.example.com",
            "api_key": "mykey",
            "user": self.user.id,
        }
        self._GET_add_object("llm_api")
        self._POST_add_object("llm_api", data["base_url"], data, "/llm_api_list")

    def test_llm_api_add_not_authenticated(self):
        """Test adding a new LLM API while not authenticated redirects to login page."""
        data = {
            "base_url": "new-llmapi.example.com",
            "api_key": "mykey",
            "user": self.user.id,
        }
        response = self.client.post(reverse("add_object", args=["llm_api"]), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/add/llm_api")

    def test_llm_api_edit_authenticated(self):
        """Test editing an existing LLM API while authenticated."""
        self.client.login(username="testuser", password="password")
        data = {
            "base_url": "edited-llmapi.example.com",
            "api_key": "mykey",
            "user": self.user.id,
        }
        self._GET_edit_object("llm_api", self.llm_api.id)
        self._POST_edit_object(
            "llm_api",
            self.llm_api.id,
            data["base_url"],
            data,
            "/llm_api_list",
        )

    def test_GET_add_invalid_object(self):
        """Verify GET request returns 404 to add invalid objects."""
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("add_object", args=["invalid_object"]))
        self.assertEqual(response.status_code, 404)

    def test_GET_edit_invalid_object(self):
        """Verify GET request returns 404 to edit invalid objects."""
        self.client.login(username="testuser", password="password")
        iid = uuid.uuid4()
        response = self.client.get(
            reverse("edit_object", args=["invalid_object", str(iid)])
        )
        self.assertEqual(response.status_code, 404)

    def test_POST_add_invalid_object(self):
        """Verify POST request returns 404 to add invalid objects."""
        self.client.login(username="testuser", password="password")
        data = {
            "object_name": "invalid_object",
        }
        response = self.client.post(
            reverse("add_object", args=["invalid_object"]), data
        )
        self.assertEqual(response.status_code, 404)

    def test_POST_edit_invalid_object(self):
        """Verify POST request returns 404 to edit invalid objects."""
        self.client.login(username="testuser", password="password")
        data = {
            "object_name": "edited-invalid_object",
        }
        iid = uuid.uuid4()
        response = self.client.post(
            reverse("edit_object", args=["invalid_object", str(iid)]), data
        )
        self.assertEqual(response.status_code, 404)


class TestDeleteObject(TestCase):
    """Tests for the delete_object view."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "testuser", "testuser@example.com", "password"
        )
        cls.bastion_host = BastionHost.objects.create(
            hostname="bastion-host.example.com", port=22, user=cls.user
        )
        cls.target_host = TargetHost.objects.create(
            hostname="target-host.example.com", port=22, user=cls.user
        )
        cls.credential = Credential.objects.create(
            credential_name="my-credential",
            username="user",
            password="pass",
            user=cls.user,
        )
        cls.llm_api = LlmApi.objects.create(
            base_url="https://api.example.com", api_key="dummy_key", user=cls.user
        )

    def _test_delete_object(self, model_name, model_instance, expected_url):
        """Test delete object functionality."""
        response = self.client.post(
            reverse("delete_object", args=[model_name, str(model_instance.id)])
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url)

        # Verify the object was deleted from the database.
        with self.assertRaises(model_instance.__class__.DoesNotExist):
            model_instance.__class__.objects.get(id=model_instance.id)

    def test_delete_bastion_host_authenticated(self):
        """Test deleting a bastion host while authenticated."""
        self.client.login(username="testuser", password="password")
        self._test_delete_object(
            "bastion_host", self.bastion_host, "/bastion_host_list"
        )

    def test_delete_bastion_host_not_authenticated(self):
        """Test deleting a bastion host while not authenticated redirects to login page."""
        response = self.client.post(
            reverse("delete_object", args=["bastion_host", str(self.bastion_host.id)])
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f"/accounts/login/?next=/delete/bastion_host/{self.bastion_host.id}",
        )

    def test_delete_target_host_authenticated(self):
        """Test deleting a target host while authenticated."""
        self.client.login(username="testuser", password="password")
        self._test_delete_object("target_host", self.target_host, "/target_host_list")

    def test_delete_target_host_not_authenticated(self):
        """Test deleting a target host while not authenticated redirects to login page."""
        response = self.client.post(
            reverse("delete_object", args=["target_host", str(self.target_host.id)])
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f"/accounts/login/?next=/delete/target_host/{self.target_host.id}"
        )

    def test_delete_credential_authenticated(self):
        """Test deleting a credential while authenticated."""
        self.client.login(username="testuser", password="password")
        self._test_delete_object("credential", self.credential, "/credential_list")

    def test_delete_credential_not_authenticated(self):
        """Test deleting a credential while not authenticated redirects to login page."""
        response = self.client.post(
            reverse("delete_object", args=["credential", str(self.credential.id)])
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f"/accounts/login/?next=/delete/credential/{self.credential.id}"
        )

    def test_delete_llm_api_authenticated(self):
        """Test deleting an LLM API while authenticated."""
        self.client.login(username="testuser", password="password")
        self._test_delete_object("llm_api", self.llm_api, "/llm_api_list")

    def test_delete_llm_api_not_authenticated(self):
        """Test deleting an LLM API while not authenticated redirects to login page."""
        response = self.client.post(
            reverse("delete_object", args=["llm_api", str(self.llm_api.id)])
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f"/accounts/login/?next=/delete/llm_api/{self.llm_api.id}"
        )

    def test_invalid_model_type(self):
        """Test for invalid model type."""
        self.client.login(username="testuser", password="password")
        response = self.client.post(
            reverse("delete_object", args=["invalid_model", str(self.bastion_host.id)])
        )
        self.assertEqual(response.status_code, 404)

    def test_invalid_uuid(self):
        """Test for invalid UUID."""
        self.client.login(username="testuser", password="password")
        non_existent_uuid = str(uuid.uuid4())
        response = self.client.post(
            reverse("delete_object", args=["bastion_host", non_existent_uuid])
        )
        self.assertEqual(response.status_code, 404)


class TestListViews(TestCase):
    """Tests for the list views."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "testuser", "testuser@example.com", "password"
        )
        cls.bastion_host = BastionHost.objects.create(
            hostname="bastion-host.example.com", port=22, user=cls.user
        )
        cls.credential = Credential.objects.create(
            credential_name="my-credential",
            username="user",
            password="pass",
            user=cls.user,
        )
        cls.llm_api = LlmApi.objects.create(
            base_url="https://api.example.com", api_key="dummy_key", user=cls.user
        )
        cls.target_host = TargetHost.objects.create(
            hostname="target-host.example.com", port=22, user=cls.user
        )
        cls.job = Job.objects.create(
            llm_api=cls.llm_api,
            user=cls.user,
            credentials_for_target_hosts=cls.credential,
        )
        cls.job.target_hosts.add(cls.target_host)

    def _test_list_view(self, view_name, expected_objects):
        """Helper function to test list views."""
        response = self.client.get(reverse(view_name))
        self.assertEqual(response.status_code, 200)
        if view_name == "job_list":
            self.assertTemplateUsed(response, "objects/job_list.html")
        else:
            self.assertTemplateUsed(response, "objects/object_list.html")
        self.assertQuerySetEqual(
            response.context["output"],
            [repr(obj) for obj in expected_objects],
            transform=repr,
            ordered=False,
        )

    def test_bastion_host_list_authenticated(self):
        """Test listing bastion hosts while authenticated."""
        self.client.login(username="testuser", password="password")
        self._test_list_view("bastion_host_list", [self.bastion_host])

    def test_bastion_host_list_not_authenticated(self):
        """Test listing bastion hosts while not authenticated redirects to login page."""
        response = self.client.get(reverse("bastion_host_list"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/bastion_host_list")

    def test_credential_list_authenticated(self):
        """Test listing credentials while authenticated."""
        self.client.login(username="testuser", password="password")
        self._test_list_view("credential_list", [self.credential])

    def test_credential_list_not_authenticated(self):
        """Test listing credentials while not authenticated redirects to login page."""
        response = self.client.get(reverse("credential_list"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/credential_list")

    def test_llm_api_list_authenticated(self):
        """Test listing LLM APIs while authenticated."""
        self.client.login(username="testuser", password="password")
        self._test_list_view("llm_api_list", [self.llm_api])

    def test_llm_api_list_not_authenticated(self):
        """Test listing LLM APIs while not authenticated redirects to login page."""
        response = self.client.get(reverse("llm_api_list"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/llm_api_list")

    def test_target_host_list_authenticated(self):
        """Test listing target hosts while authenticated."""
        self.client.login(username="testuser", password="password")
        self._test_list_view("target_host_list", [self.target_host])

    def test_target_host_list_not_authenticated(self):
        """Test listing target hosts while not authenticated redirects to login page."""
        response = self.client.get(reverse("target_host_list"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/target_host_list")

    def test_job_list_authenticated(self):
        """Test listing jobs while authenticated."""
        self.client.login(username="testuser", password="password")
        self._test_list_view("job_list", [self.job])

    def test_job_list_not_authenticated(self):
        """Test listing jobs while not authenticated redirects to login page."""
        response = self.client.get(reverse("job_list"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/job_list")

    def test_empty_bastion_host_list(self):
        """Test listing bastion hosts when none exist."""
        self.client.login(username="testuser", password="password")
        BastionHost.objects.all().delete()
        self._test_list_view("bastion_host_list", [])

    def test_empty_credential_list(self):
        """Test listing credentials when none exist."""
        self.client.login(username="testuser", password="password")
        Credential.objects.all().delete()
        self._test_list_view("credential_list", [])

    def test_empty_llm_api_list(self):
        """Test listing LLM APIs when none exist."""
        self.client.login(username="testuser", password="password")
        LlmApi.objects.all().delete()
        self._test_list_view("llm_api_list", [])

    def test_empty_target_host_list(self):
        """Test listing target hosts when none exist."""
        self.client.login(username="testuser", password="password")
        TargetHost.objects.all().delete()
        self._test_list_view("target_host_list", [])

    def test_empty_job_list(self):
        """Test listing jobs when none exist."""
        self.client.login(username="testuser", password="password")
        Job.objects.all().delete()
        self._test_list_view("job_list", [])


class TestHomeView(TestCase):
    """Tests for the home view."""

    def setUp(self):
        self.user = User.objects.create_user(
            "testuser", "testuser@example.com", "password"
        )

    def test_home_view_authenticated(self):
        """Test home view while authenticated returns 200."""
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_home_view_not_authenticated(self):
        """Test home view while not authenticated redirects to login page."""
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/home")


class TestLandingView(TestCase):
    """Tests for the landing page view."""

    def test_landing_view_authenticated(self):
        """Test landing page view while authenticated returns 200."""
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "landing.html")

    def test_landing_view_not_authenticated(self):
        """Test landing page view while not authenticated returns 200."""
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "landing.html")


class TestCreateJobView(TestCase):
    """Tests for the create_job view."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "testuser", "testuser@example.com", "password"
        )
        cls.llm_api = LlmApi.objects.create(
            base_url="https://api.example.com", api_key="dummy_key", user=cls.user
        )
        cls.credential = Credential.objects.create(
            credential_name="my-credential",
            username="user",
            password="pass",
            user=cls.user,
        )
        cls.target_host1 = TargetHost.objects.create(
            hostname="target-host1.example.com", port=22, user=cls.user
        )
        cls.target_host2 = TargetHost.objects.create(
            hostname="target-host2.example.com", port=22, user=cls.user
        )

    def test_create_single_job_authenticated(self):
        """Test creating a single job with one target host while authenticated."""
        self.client.login(username="testuser", password="password")
        data = {
            "llm_api": self.llm_api.id,
            "credentials_for_target_hosts": self.credential.id,
            "target_hosts": [self.target_host1.id],
            "user": self.user.id,
            "instructions": "Test instructions",
        }
        response = self.client.post(reverse("create_job"), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/job_list")

        # Verify the job is created
        job = Job.objects.get()
        self.assertEqual(job.status, "Pending")
        self.assertEqual(job.llm_api, self.llm_api)
        self.assertIn(self.target_host1, job.target_hosts.all())  # codespell:ignore

    def test_create_single_job_not_authenticated(self):
        """Test creating a single job with one target host while not authenticated redirects to login."""
        data = {
            "llm_api": self.llm_api.id,
            "credentials_for_target_hosts": self.credential.id,
            "target_hosts": [self.target_host1.id],
            "user": self.user.id,
            "instructions": "Test instructions",
        }
        response = self.client.post(reverse("create_job"), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/add/job")

    def test_get_create_job_view_authenticated(self):
        """Test accessing the create job view with a GET request while authenticated."""
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("create_job"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "objects/add_object.html")

    def test_get_create_job_view_not_authenticated(self):
        """Test accessing the create job view with a GET request while not authenticated redirects to login."""
        response = self.client.get(reverse("create_job"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/add/job")


class TestRequestJob(TestCase):
    def setUp(self):
        # Set up initial data.
        self.user = User.objects.create(email="testuser@example.com")
        self.llm_api = LlmApi.objects.create(
            base_url="http://api.example.com", api_key="apikey123", user=self.user
        )
        self.bastion_host = BastionHost.objects.create(
            hostname="bastion.example.com", user=self.user, port=22
        )
        self.credential = Credential.objects.create(
            credential_name="admin",
            user=self.user,
            username="admin",
            password="password",
        )
        self.target_host = TargetHost.objects.create(
            hostname="target.example.com", user=self.user, port=22
        )

        self.job1 = Job.objects.create(
            status="Running",
            llm_api=self.llm_api,
            bastion_host=self.bastion_host,
            credentials_for_bastion_host=self.credential,
            credentials_for_target_hosts=self.credential,
            instructions="Job 1 instructions",
            user=self.user,
        )
        self.job1.target_hosts.add(self.target_host)

        self.job2 = Job.objects.create(
            status="Pending",
            llm_api=self.llm_api,
            bastion_host=self.bastion_host,
            credentials_for_bastion_host=self.credential,
            credentials_for_target_hosts=self.credential,
            instructions="Job 2 instructions",
            user=self.user,
        )
        self.job2.target_hosts.add(self.target_host)

        self.job3 = Job.objects.create(
            status="Pending",
            llm_api=self.llm_api,
            bastion_host=self.bastion_host,
            credentials_for_bastion_host=self.credential,
            credentials_for_target_hosts=self.credential,
            instructions="Job 3 instructions",
            user=self.user,
        )
        self.job3.target_hosts.add(self.target_host)

    def test_no_private_key_provided(self):
        """Test that 400 is returned if no private key is provided."""
        """Test that 404 is returned if no private key is provided."""
        response = self.client.get(reverse("request_job"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"], "Authorization header not provided."
        )

    def test_incorrect_private_key(self):
        """Test that 404 is returned if an incorrect private key is provided."""
        headers = {"HTTP_AUTHORIZATION": "Bearer wrongprivatekey"}
        response = self.client.get(reverse("request_job"), **headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Authorization token incorrect.")

    def test_oldest_pending_job_is_returned(self):
        """Test that the oldest pending job is returned."""
        headers = {"HTTP_AUTHORIZATION": "Bearer myprivatekey"}
        response = self.client.get(reverse("request_job"), **headers)
        self.assertEqual(response.status_code, 200)
        job_data = json.loads(response.content)

        self.assertEqual(job_data["id"], str(self.job2.id))
        self.assertEqual(job_data["instructions"], self.job2.instructions)
        self.assertEqual(job_data["llm_api_baseurl"], self.llm_api.base_url)
        self.assertEqual(job_data["llm_api_api_key"], self.llm_api.api_key)
        self.assertEqual(job_data["bastion_host_hostname"], self.bastion_host.hostname)
        self.assertEqual(job_data["bastion_host_port"], self.bastion_host.port)
        self.assertEqual(
            job_data["credentials_for_bastion_host_username"], self.credential.username
        )
        self.assertEqual(
            job_data["credentials_for_bastion_host_password"], self.credential.password
        )
        self.assertEqual(job_data["target_host_hostname"], self.target_host.hostname)
        self.assertEqual(job_data["target_host_port"], self.target_host.port)
        self.assertEqual(
            job_data["credentials_for_target_hosts_username"], self.credential.username
        )
        self.assertEqual(
            job_data["credentials_for_target_hosts_password"], self.credential.password
        )

    def test_no_pending_jobs(self):
        """Test that 404 is returned if no pending jobs are found."""
        Job.objects.all().delete()
        headers = {"HTTP_AUTHORIZATION": "Bearer myprivatekey"}
        response = self.client.get(reverse("request_job"), **headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "No pending jobs found.")

    @patch(
        "ssherlock_server.views.Job.objects.filter",
        side_effect=Exception("Test exception"),
    )
    def test_request_job_exception_handling(self, _):
        """Test that an exception in request_job returns a 500 status code."""
        headers = {"HTTP_AUTHORIZATION": f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}"}
        response = self.client.get(reverse("request_job"), **headers)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["message"], "Test exception")


class TestUpdateJobStatus(TestCase):
    def setUp(self):
        self.client = Client()
        self.invalid_private_key = "Bearer wrongkey"
        self.user = User.objects.create(email="testuser@example.com")
        self.llm_api = LlmApi.objects.create(
            base_url="http://api.example.com", api_key="apikey123", user=self.user
        )
        self.bastion_host = BastionHost.objects.create(
            hostname="bastion.example.com", user=self.user, port=22
        )
        self.credential = Credential.objects.create(
            credential_name="admin",
            user=self.user,
            username="admin",
            password="password",
        )
        self.target_host = TargetHost.objects.create(
            hostname="target.example.com", user=self.user, port=22
        )

        self.job1 = Job.objects.create(
            status="Running",
            llm_api=self.llm_api,
            bastion_host=self.bastion_host,
            credentials_for_bastion_host=self.credential,
            credentials_for_target_hosts=self.credential,
            instructions="Job 1 instructions",
            user=self.user,
        )
        self.job1.target_hosts.add(self.target_host)
        self.url = reverse("update_job_status", args=[self.job1.id])

        self.job2 = Job.objects.create(
            status="Pending",
            llm_api=self.llm_api,
            bastion_host=self.bastion_host,
            credentials_for_bastion_host=self.credential,
            credentials_for_target_hosts=self.credential,
            instructions="Job 1 instructions",
            user=self.user,
        )
        self.job2.target_hosts.add(self.target_host)
        self.url2 = reverse("update_job_status", args=[self.job2.id])

    def test_update_job_status_to_completed_with_valid_key_and_status(self):
        """Test updating job status to Completed with a valid key and status."""
        response = self.client.post(
            self.url,
            data=json.dumps({"status": "Completed"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}",
        )
        self.assertEqual(response.status_code, 200)
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.status, "Completed")

    def test_update_job_status_to_canceled_with_valid_key_and_status(self):
        """Test updating job status to Canceled with a valid key and status."""
        response = self.client.post(
            self.url,
            data=json.dumps({"status": "Canceled"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}",
        )
        self.assertEqual(response.status_code, 200)
        self.job1.refresh_from_db()
        self.assertEqual(self.job1.status, "Canceled")

    def test_update_job_status_to_invalid_status(self):
        """Test updating job status with an invalid status."""
        response = self.client.post(
            self.url2,
            data=json.dumps({"status": "INVALID"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}",
        )
        self.assertEqual(response.status_code, 400)

    def test_update_job_status_with_invalid_key(self):
        """Test updating job status with an invalid key."""
        response = self.client.post(
            self.url,
            data=json.dumps({"status": "Completed"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=self.invalid_private_key,
        )
        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(
            response.content.decode("utf-8"),
            '{"message": "Authorization token incorrect."}',
        )

    def test_update_job_status_without_key(self):
        """Test updating job status without providing a key."""
        response = self.client.post(
            self.url,
            data=json.dumps({"status": "Completed"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode("utf-8"),
            '{"message": "Authorization header not provided."}',
        )

    def test_update_job_status_with_invalid_header_format(self):
        """Test updating job status with an invalid header format."""
        response = self.client.post(
            self.url,
            data=json.dumps({"status": "Completed"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="InvalidFormatKey",
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode("utf-8"),
            '{"message": "Invalid Authorization header format."}',
        )

    def test_update_job_status_without_status(self):
        """Test updating job status without providing a status."""
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content.decode("utf-8"), '{"message": "Status not provided."}'
        )

    def test_update_job_status_with_invalid_job_id(self):
        """Test updating job status with an invalid job ID."""
        # Create an invalid UUID by modifying the last character
        invalid_uuid = str(self.job1.id)[:-6] + "abcdef"
        invalid_url = reverse("update_job_status", args=[invalid_uuid])
        response = self.client.post(
            invalid_url,
            data=json.dumps({"status": "Completed"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}",
        )
        self.assertEqual(response.status_code, 500)

    def test_update_job_status_to_running_also_adds_started_at_time(self):
        """Test updating job status to Running also adds started_at time."""
        response = self.client.post(
            self.url2,
            data=json.dumps({"status": "Running"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}",
        )

        self.job2.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.job2.status, "Running")
        self.assertIsNotNone(self.job2.started_at)
        self.assertTrue(
            timezone.now() - self.job2.started_at < timezone.timedelta(seconds=1)
        )

    def test_update_job_status_to_completed_also_adds_completed_at_time(self):
        """Test updating job status to Completed also adds completed_at time."""
        response = self.client.post(
            self.url2,
            data=json.dumps({"status": "Completed"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}",
        )

        self.job2.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.job2.status, "Completed")
        self.assertIsNotNone(self.job2.completed_at)
        self.assertTrue(
            timezone.now() - self.job2.completed_at < timezone.timedelta(seconds=1)
        )

    def test_update_job_status_to_failed_also_adds_stopped_at_time(self):
        """Test updating job status to Failed also adds stopped_at time."""
        response = self.client.post(
            self.url2,
            data=json.dumps({"status": "Failed"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}",
        )

        self.job2.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.job2.status, "Failed")
        self.assertIsNotNone(self.job2.stopped_at)
        self.assertTrue(
            timezone.now() - self.job2.stopped_at < timezone.timedelta(seconds=1)
        )


class TestGetJobStatus(TestCase):
    def setUp(self):
        # Set up initial data.
        self.user = User.objects.create(email="testuser@example.com")
        self.llm_api = LlmApi.objects.create(
            base_url="http://api.example.com", api_key="apikey123", user=self.user
        )
        self.bastion_host = BastionHost.objects.create(
            hostname="bastion.example.com", user=self.user, port=22
        )
        self.credential = Credential.objects.create(
            credential_name="admin",
            user=self.user,
            username="admin",
            password="password",
        )
        self.target_host = TargetHost.objects.create(
            hostname="target.example.com", user=self.user, port=22
        )

        self.job1 = Job.objects.create(
            status="Running",
            llm_api=self.llm_api,
            bastion_host=self.bastion_host,
            credentials_for_bastion_host=self.credential,
            credentials_for_target_hosts=self.credential,
            instructions="Job 1 instructions",
            user=self.user,
        )
        self.job1.target_hosts.add(self.target_host)

        self.client = Client()

    def test_no_private_key_provided(self):
        """Test that 404 is returned if no private key is provided."""
        response = self.client.get(reverse("get_job_status", args=[self.job1.id]))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"], "Authorization header not provided."
        )

    def test_incorrect_private_key(self):
        """Test that 404 is returned if an incorrect private key is provided."""
        headers = {"HTTP_AUTHORIZATION": "Bearer wrongprivatekey"}
        response = self.client.get(
            reverse("get_job_status", args=[self.job1.id]), **headers
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["message"], "Authorization token incorrect.")

    def test_get_job_status_success(self):
        """Test that job status is returned successfully with correct private key."""
        headers = {"HTTP_AUTHORIZATION": f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}"}
        response = self.client.get(
            reverse("get_job_status", args=[self.job1.id]), **headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], self.job1.status)

    def test_job_not_found(self):
        """Test that 500 is returned if job is not found."""
        headers = {"HTTP_AUTHORIZATION": f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}"}
        invalid_uuid = str(self.job1.id)[:-12] + "123456abcdef"
        response = self.client.get(
            reverse("get_job_status", args=[invalid_uuid]), **headers
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["message"], "No Job matches the given query.")


class TestRetryJob(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            "testuser", "testuser@example.com", "password"
        )
        self.llm_api = LlmApi.objects.create(
            base_url="http://api.example.com", api_key="apikey123", user=self.user
        )
        self.bastion_host = BastionHost.objects.create(
            hostname="bastion.example.com", user=self.user, port=22
        )
        self.credential = Credential.objects.create(
            credential_name="admin",
            user=self.user,
            username="admin",
            password="password",
        )
        self.target_host = TargetHost.objects.create(
            hostname="target.example.com", user=self.user, port=22
        )

        self.failed_job = Job.objects.create(
            status="Failed",
            llm_api=self.llm_api,
            bastion_host=self.bastion_host,
            credentials_for_bastion_host=self.credential,
            credentials_for_target_hosts=self.credential,
            instructions="Job 1 instructions",
            user=self.user,
        )
        self.failed_job.target_hosts.add(self.target_host)

        self.completed_job = Job.objects.create(
            status="Completed",
            llm_api=self.llm_api,
            bastion_host=self.bastion_host,
            credentials_for_bastion_host=self.credential,
            credentials_for_target_hosts=self.credential,
            instructions="Job 2 instructions",
            user=self.user,
        )
        self.completed_job.target_hosts.add(self.target_host)

    def test_retry_failed_job_authenticated(self):
        """Test retrying a failed job while authenticated changes its status to Pending."""
        self.client.login(username="testuser", password="password")
        self.assertEqual(self.failed_job.status, "Failed")
        response = self.client.get(reverse("retry_job", args=[self.failed_job.pk]))
        self.failed_job.refresh_from_db()
        self.assertEqual(self.failed_job.status, "Pending")
        self.assertEqual(response.status_code, 302)

    def test_retry_failed_job_not_authenticated(self):
        """Test retrying a failed job while not authenticated redirects to login page."""
        response = self.client.get(reverse("retry_job", args=[self.failed_job.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f"/accounts/login/?next=/retry/job/{self.failed_job.pk}"
        )

    def test_retry_non_failed_job_does_not_change_status(self):
        """Test retrying a non-failed job does not change its status."""
        self.client.login(username="testuser", password="password")
        self.assertEqual(self.completed_job.status, "Completed")
        self.client.get(reverse("retry_job", args=[self.completed_job.pk]))
        self.completed_job.refresh_from_db()
        self.assertEqual(self.completed_job.status, "Completed")

    def test_retry_job_non_existent_job(self):
        """Test retrying a non-existent job returns 404."""
        self.client.login(username="testuser", password="password")
        invalid_uuid = "00000000-0000-0000-0000-000000000000"
        response = self.client.get(reverse("retry_job", args=[invalid_uuid]))
        self.assertEqual(response.status_code, 404)

    def test_retry_job_correct_response(self):
        """Test retrying a job returns the correct response."""
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("retry_job", args=[self.failed_job.pk]))
        self.assertEqual(response.status_code, 302)


class TestCancelJob(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            "testuser", "testuser@example.com", "password"
        )
        self.llm_api = LlmApi.objects.create(
            base_url="http://api.example.com", api_key="apikey123", user=self.user
        )
        self.bastion_host = BastionHost.objects.create(
            hostname="bastion.example.com", user=self.user, port=22
        )
        self.credential = Credential.objects.create(
            credential_name="admin",
            user=self.user,
            username="admin",
            password="password",
        )
        self.target_host = TargetHost.objects.create(
            hostname="target.example.com", user=self.user, port=22
        )

        self.running_job = Job.objects.create(
            status="Running",
            llm_api=self.llm_api,
            bastion_host=self.bastion_host,
            credentials_for_bastion_host=self.credential,
            credentials_for_target_hosts=self.credential,
            instructions="Job 1 instructions",
            user=self.user,
        )
        self.running_job.target_hosts.add(self.target_host)

        self.completed_job = Job.objects.create(
            status="Completed",
            llm_api=self.llm_api,
            bastion_host=self.bastion_host,
            credentials_for_bastion_host=self.credential,
            credentials_for_target_hosts=self.credential,
            instructions="Job 2 instructions",
            user=self.user,
        )
        self.completed_job.target_hosts.add(self.target_host)

    def test_cancel_running_job_authenticated(self):
        """Test canceling a running job while authenticated changes status to Canceled."""
        self.client.login(username="testuser", password="password")
        self.assertEqual(self.running_job.status, "Running")
        response = self.client.get(
            reverse("cancel_job", args=[self.running_job.pk]), HTTP_REFERER="/job_list"
        )
        self.running_job.refresh_from_db()
        self.assertEqual(self.running_job.status, "Canceled")
        self.assertEqual(response.status_code, 302)

    def test_cancel_running_job_not_authenticated(self):
        """Test canceling a running job while not authenticated redirects to login page."""
        response = self.client.get(reverse("cancel_job", args=[self.running_job.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f"/accounts/login/?next=/cancel_job/{self.running_job.pk}"
        )

    def test_cancel_completed_job_authenticated(self):
        """Test canceling a completed job while authenticated does not change status."""
        self.client.login(username="testuser", password="password")
        self.assertEqual(self.completed_job.status, "Completed")
        response = self.client.get(
            reverse("cancel_job", args=[self.completed_job.pk]),
            HTTP_REFERER="/job_list",
        )
        self.completed_job.refresh_from_db()
        self.assertEqual(self.completed_job.status, "Completed")
        self.assertEqual(response.status_code, 302)

    def test_cancel_completed_job_not_authenticated(self):
        """Test canceling a completed job while not authenticated redirects to login page."""
        response = self.client.get(reverse("cancel_job", args=[self.completed_job.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f"/accounts/login/?next=/cancel_job/{self.completed_job.pk}"
        )

    def test_cancel_non_existent_job_authenticated(self):
        """Test canceling a non-existent job while authenticated returns 404."""
        self.client.login(username="testuser", password="password")
        invalid_uuid = "00000000-0000-0000-0000-000000000000"
        response = self.client.get(reverse("cancel_job", args=[invalid_uuid]))
        self.assertEqual(response.status_code, 404)

    def test_cancel_job_no_http_referer(self):
        """Test canceling a job without HTTP_REFERER redirects to job list."""
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("cancel_job", args=[self.running_job.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/job_list")


class TestLogJobData(TestCase):
    def setUp(self):
        self.client = Client()
        self.job_id = "f6e752d6-b065-4c49-9241-e4eefbc274e3"
        self.valid_log_content = {"log": "This is a log entry."}
        self.invalid_log_content = {"invalid_key": "No log here."}
        self.url = reverse("log_job_data", args=[self.job_id])
        self.valid_token = "Bearer myprivatekey"
        self.invalid_token = "Bearer wrongprivatekey"

        # Define expected log directory and file path
        self.log_dir = os.path.join(
            settings.BASE_DIR.parent,
            "ssherlock_runner_job_logs",
            self.job_id[0:2],
            self.job_id[2:4],
            self.job_id[4:6],
        )
        self.log_file_path = os.path.join(self.log_dir, f"{self.job_id[6:]}.log")

    @patch("ssherlock_server.utils.check_private_key")
    def test_valid_log_entry(self, mock_check_private_key):
        mock_check_private_key.return_value = None

        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_log_content),
            content_type="application/json",
            HTTP_AUTHORIZATION=self.valid_token,
        )

        # Ensure the response is successful
        self.assertEqual(response.status_code, 200)

        # Check if the log directory exists
        self.assertTrue(os.path.isdir(self.log_dir))

        # Check if the log file exists and contains the correct data
        self.assertTrue(os.path.isfile(self.log_file_path))
        with open(self.log_file_path, "r", encoding="utf-8") as log_file:
            content = log_file.read()
            self.assertIn(self.valid_log_content["log"], content)

    @patch("ssherlock_server.utils.check_private_key")
    def test_missing_log_content(self, mock_check_private_key):
        mock_check_private_key.return_value = None
        response = self.client.post(
            self.url,
            data=json.dumps(self.invalid_log_content),
            content_type="application/json",
            HTTP_AUTHORIZATION=self.valid_token,
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {"message": "Log content not provided."})

    @patch("ssherlock_server.utils.check_private_key")
    def test_invalid_authorization(self, mock_check_private_key):
        mock_check_private_key.return_value = JsonResponse(
            {"message": "Authorization token incorrect."}, status=404
        )
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_log_content),
            content_type="application/json",
            HTTP_AUTHORIZATION=self.invalid_token,
        )
        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(
            response.content, {"message": "Authorization token incorrect."}
        )

    @patch("ssherlock_server.utils.check_private_key")
    def test_no_authorization_header(self, mock_check_private_key):
        mock_check_private_key.return_value = None
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_log_content),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content, {"message": "Authorization header not provided."}
        )

    @patch("ssherlock_server.utils.check_private_key")
    def test_exception_handling(self, mock_check_private_key):
        """Test exception handling in log job data."""
        mock_check_private_key.return_value = None

        with patch(
            "ssherlock_server.views.open", side_effect=Exception("Test exception")
        ):
            response = self.client.post(
                self.url,
                data=json.dumps(self.valid_log_content),
                content_type="application/json",
                HTTP_AUTHORIZATION=self.valid_token,
            )
            self.assertEqual(response.status_code, 500)
            self.assertJSONEqual(response.content, {"message": "Test exception"})

    def tearDown(self):
        # Clean up by removing the created log file and directories
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)
        if os.path.exists(self.log_dir):
            os.removedirs(self.log_dir)


class TestViewJob(TestCase):
    """Tests for the view_job function."""

    def setUp(self):
        # Set up initial data.
        self.user = User.objects.create_user(
            "testuser", "testuser@example.com", "password"
        )
        self.llm_api = LlmApi.objects.create(
            base_url="http://api.example.com", api_key="apikey123", user=self.user
        )
        self.bastion_host = BastionHost.objects.create(
            hostname="bastion.example.com", user=self.user, port=22
        )
        self.credential = Credential.objects.create(
            credential_name="admin",
            user=self.user,
            username="admin",
            password="password",
        )
        self.target_host = TargetHost.objects.create(
            hostname="target.example.com", user=self.user, port=22
        )

        self.job = Job.objects.create(
            status="Running",
            llm_api=self.llm_api,
            bastion_host=self.bastion_host,
            credentials_for_bastion_host=self.credential,
            credentials_for_target_hosts=self.credential,
            instructions="Job 1 instructions",
            user=self.user,
        )
        self.job.target_hosts.add(self.target_host)

    def test_view_existing_job_authenticated(self):
        """Test viewing a job while authenticated returns 200."""
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("view_job", args=[str(self.job.id)]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "objects/view_job.html")

    def test_view_existing_job_not_authenticated(self):
        """Test viewing a job while not authenticated redirects to login page."""
        response = self.client.get(reverse("view_job", args=[str(self.job.id)]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"/accounts/login/?next=/view_job/{self.job.id}")

    def test_view_nonexistent_job_authenticated(self):
        """Test viewing a nonexistent job while authenticated returns 404."""
        """Test viewing a nonexistent job while authenticated returns 404."""
        self.client.login(username="testuser", password="password")
        non_existent_job_id = uuid.uuid4()
        response = self.client.get(reverse("view_job", args=[str(non_existent_job_id)]))
        self.assertEqual(response.status_code, 404)


class TestStreamJobLog(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "testuser", "testuser@example.com", "password"
        )
        self.client = Client()
        self.job_id = "0d7420d5-f24b-4b8e-8e50-bb0a20575b54"

    @patch(
        "builtins.open", new_callable=mock_open, read_data="Log entry 1\nLog entry 2\n"
    )
    def test_stream_job_log_authenticated(self, _):
        """Test streaming job log while authenticated."""
        self.client.login(username="testuser", password="password")
        with patch(
            "builtins.open",
            new_callable=mock_open,
            read_data="Log entry 1\nLog entry 2\n",
        ):
            response = self.client.get(
                reverse("stream_job_log", args=[self.job_id]), stream=True
            )

            # Collect a finite number of lines from the stream
            content = []
            for chunk in response.streaming_content:
                content.append(chunk.decode("utf-8"))
                if len(content) >= 2:  # Limit to two lines for the test
                    break

            combined_content = "".join(content)
            self.assertIn("data: Log entry 1", combined_content)
            self.assertIn("data: Log entry 2", combined_content)

    def test_stream_job_log_not_authenticated(self):
        """Test streaming job log while not authenticated redirects to login page."""
        response = self.client.get(reverse("stream_job_log", args=[self.job_id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, f"/accounts/login/?next=/view_job/{self.job_id}/log"
        )

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_stream_job_log_file_not_found(self, _):
        """Test streaming of job log when file does not exist."""
        self.client.login(username="testuser", password="password")
        response = self.client.get(
            reverse("stream_job_log", args=[self.job_id]), stream=True
        )

        # Collect a finite number of lines from the stream
        content = []
        for chunk in response.streaming_content:
            content.append(chunk.decode("utf-8"))
            if "event: error" in chunk.decode("utf-8"):
                break

        combined_content = "".join(content)
        self.assertIn("event: error", combined_content)
        self.assertIn("data: Log file not found", combined_content)


class TestSignupView(TestCase):
    """Tests for the signup view."""

    def setUp(self):
        self.client = Client()

    def test_signup_page_renders_correctly(self):
        """Test that the signup page renders correctly."""
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "signup.html")

    def test_signup_successful(self):
        """Test that a user can sign up successfully."""
        response = self.client.post(
            reverse("signup"),
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "complexpassword123",
                "password2": "complexpassword123",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_signup_password_mismatch(self):
        """Test that signup fails if passwords do not match."""
        response = self.client.post(
            reverse("signup"),
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "complexpassword123",
                "password2": "differentpassword123",
            },
        )
        self.assertEqual(response.status_code, 200)
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertTrue(form.errors)
        self.assertIn("password2", form.errors)
        self.assertEqual(form.errors["password2"], ["The two password fields didn’t match."])
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_signup_existing_username(self):
        """Test that signup fails if the username already exists."""
        User.objects.create_user("existinguser", "existinguser@example.com", "password")
        response = self.client.post(
            reverse("signup"),
            data={
                "username": "existinguser",
                "email": "newuser@example.com",
                "password1": "complexpassword123",
                "password2": "complexpassword123",
            },
        )
        self.assertEqual(response.status_code, 200)
        form = response.context.get('form')
        self.assertIsNotNone(form)
        self.assertTrue(form.errors)
        self.assertIn("username", form.errors)
        self.assertEqual(form.errors["username"], ["A user with that username already exists."])


class TestAccountView(TestCase):
    """Tests for the account view."""

    def setUp(self):
        self.user = User.objects.create_user(
            "testuser", "testuser@example.com", "password"
        )
        self.client = Client()

    def test_account_view_authenticated(self):
        """Test account view while authenticated returns 200."""
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("account"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account.html")
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.email)

    def test_account_view_not_authenticated(self):
        """Test account view while not authenticated redirects to login page."""
        response = self.client.get(reverse("account"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/accounts/login/?next=/account/")
