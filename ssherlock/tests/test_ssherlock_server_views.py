from django.test import TestCase, Client
from django.urls import reverse
from ssherlock_server.models import (
    User,
    BastionHost,
    Credential,
    Job,
    LlmApi,
    TargetHost,
)
from ssherlock_server.forms import (
    BastionHostForm,
    CredentialForm,
    JobForm,
    LlmApiForm,
    TargetHostForm,
)
from ssherlock_server.views import handle_object
import uuid


class TestHandleObject(TestCase):
    """Tests for the handle_object view."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(email="user@example.com")
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
        self.assertTemplateUsed(response, f"ssherlock_server/objects/add_object.html")

    def _GET_edit_object(self, model_name, uuid):
        """Verify GET requests work to edit objects."""
        response = self.client.get(reverse("edit_object", args=[model_name, str(uuid)]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ssherlock_server/objects/edit_object.html")

    def _POST_add_object(self, model_name, new_object_str, data, expected_url):
        """Verify POSTS requests work to add objects."""
        response_add = self.client.post(reverse("add_object", args=[model_name]), data)
        self.assertEqual(response_add.status_code, 302)
        self.assertRedirects(response_add, expected_url)
        # Verify the newly-added object appears in the list of objects now.
        response_list = self.client.get(reverse(f"{model_name}_list"))
        self.assertContains(response_list, new_object_str)

    def _POST_edit_object(
        self, model_name, uuid, edited_object_str, data, expected_url
    ):
        """Verify POSTS requests work to edit objects."""
        response = self.client.post(
            reverse("edit_object", args=[model_name, str(uuid)]), data
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_url)
        # Verify the newly-edited object appears in the list of objects now.
        response_list = self.client.get(reverse(f"{model_name}_list"))
        self.assertContains(response_list, edited_object_str)

    # #########################################################################
    # Main test functions.
    # #########################################################################

    def test_bastion_host_add(self):
        data = {
            "hostname": "new-bastion_host.example.com",
            "port": 22,
            "user": self.user.id,
        }
        self._GET_add_object("bastion_host")
        self._POST_add_object(
            "bastion_host", data["hostname"], data, "/bastion_host_list"
        )

    def test_bastion_host_edit(self):
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

    def test_target_host_add(self):
        data = {
            "hostname": "new-target_host.example.com",
            "port": 22,
            "user": self.user.id,
        }
        self._GET_add_object("target_host")
        self._POST_add_object(
            "target_host", data["hostname"], data, "/target_host_list"
        )

    def test_target_host_edit(self):
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

    def test_credential_add(self):
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

    def test_credential_edit(self):
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

    def test_llm_api_add(self):
        data = {
            "base_url": "new-llmapi.example.com",
            "api_key": "mykey",
            "user": self.user.id,
        }
        self._GET_add_object("llm_api")
        self._POST_add_object("llm_api", data["base_url"], data, "/llm_api_list")

    def test_llm_api_edit(self):
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
        response = self.client.get(reverse("add_object", args=["invalid_object"]))
        self.assertEqual(response.status_code, 404)

    def test_GET_edit_invalid_object(self):
        """Verify GET request returns 404 to edit invalid objects."""
        iid = uuid.uuid4()
        response = self.client.get(
            reverse("edit_object", args=["invalid_object", str(iid)])
        )
        self.assertEqual(response.status_code, 404)

    def test_POST_add_invalid_object(self):
        """Verify POST request returns 404 to add invalid objects."""
        data = {
            "object_name": "invalid_object",
        }
        response = self.client.post(
            reverse("add_object", args=["invalid_object"]), data
        )
        self.assertEqual(response.status_code, 404)

    def test_POST_edit_invalid_object(self):
        """Verify POST request returns 404 to edit invalid objects."""
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
        cls.user = User.objects.create(email="user@example.com")
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

    def test_delete_bastion_host(self):
        self._test_delete_object(
            "bastion_host", self.bastion_host, "/bastion_host_list"
        )

    def test_delete_target_host(self):
        self._test_delete_object("target_host", self.target_host, "/target_host_list")

    def test_delete_credential(self):
        self._test_delete_object("credential", self.credential, "/credential_list")

    def test_delete_llm_api(self):
        self._test_delete_object("llm_api", self.llm_api, "/llm_api_list")

    def test_invalid_model_type(self):
        """Test for invalid model type."""
        response = self.client.post(
            reverse("delete_object", args=["invalid_model", str(self.bastion_host.id)])
        )
        self.assertEqual(response.status_code, 404)

    def test_invalid_uuid(self):
        """Test for invalid UUID."""
        non_existent_uuid = str(uuid.uuid4())
        response = self.client.post(
            reverse("delete_object", args=["bastion_host", non_existent_uuid])
        )
        self.assertEqual(response.status_code, 404)


class TestListViews(TestCase):
    """Tests for the list views."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(email="user@example.com")
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
        self.assertTemplateUsed(response, "ssherlock_server/objects/object_list.html")
        self.assertQuerySetEqual(
            response.context["output"],
            [repr(obj) for obj in expected_objects],
            transform=repr,
            ordered=False,
        )

    def test_bastion_host_list(self):
        self._test_list_view("bastion_host_list", [self.bastion_host])

    def test_credential_list(self):
        self._test_list_view("credential_list", [self.credential])

    def test_llm_api_list(self):
        self._test_list_view("llm_api_list", [self.llm_api])

    def test_target_host_list(self):
        self._test_list_view("target_host_list", [self.target_host])

    def test_job_list(self):
        self._test_list_view("job_list", [self.job])

    def test_empty_bastion_host_list(self):
        BastionHost.objects.all().delete()
        self._test_list_view("bastion_host_list", [])

    def test_empty_credential_list(self):
        Credential.objects.all().delete()
        self._test_list_view("credential_list", [])

    def test_empty_llm_api_list(self):
        LlmApi.objects.all().delete()
        self._test_list_view("llm_api_list", [])

    def test_empty_target_host_list(self):
        TargetHost.objects.all().delete()
        self._test_list_view("target_host_list", [])

    def test_empty_job_list(self):
        Job.objects.all().delete()
        self._test_list_view("job_list", [])


class TestCreateJobView(TestCase):
    """Tests for the create_job view."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(email="user@example.com")
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

    def test_create_single_job(self):
        """Test creating a single job with one target host."""
        data = {
            "llm_api": self.llm_api.id,
            "credentials_for_target_hosts": self.credential.id,
            "target_hosts": [self.target_host1.id],
            "user": self.user.id,
            "instructions": "Test instructions"
        }
        response = self.client.post(reverse("create_job"), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/job_list")

        # Verify the job is created
        job = Job.objects.get()
        self.assertEqual(job.status, "PENDING")
        self.assertEqual(job.llm_api, self.llm_api)
        self.assertIn(self.target_host1, job.target_hosts.all()) # codespell:ignore

    def test_create_multiple_jobs(self):
        """Test creating multiple jobs with multiple target hosts."""
        data = {
            "status": "Pending",
            "llm_api": self.llm_api.id,
            "credentials_for_target_hosts": [self.credential.id],
            "target_hosts": [self.target_host1.id, self.target_host2.id],
            "user": self.user.id,
            "instructions": "Test instructions"
        }
        response = self.client.post(reverse("create_job"), data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/job_list")

        # Verify two jobs are created
        jobs = Job.objects.all()
        self.assertEqual(jobs.count(), 2)

        # Check the first job
        job1 = jobs[0]
        self.assertEqual(job1.status, "PENDING")
        self.assertEqual(job1.llm_api, self.llm_api)
        self.assertIn(self.target_host1, job1.target_hosts.all()) # codespell:ignore

        # Check the second job
        job2 = jobs[1]
        self.assertEqual(job2.status, "PENDING")
        self.assertEqual(job2.llm_api, self.llm_api)
        self.assertIn(self.target_host2, job2.target_hosts.all()) # codespell:ignore


    def test_invalid_form_submission(self):
        """Test form submission with invalid data."""
        data = {
            "status": "Pending",
            "llm_api": "",
            "credentials_for_target_hosts": [self.credential.id],
            "target_hosts": [self.target_host1.id],
        }
        response = self.client.post(reverse("create_job"), data)
        self.assertEqual(response.status_code, 200)  # Form should return with errors
        self.assertTemplateUsed(response, "ssherlock_server/objects/add_object.html")

        # Verify no job is created
        jobs = Job.objects.all()
        self.assertEqual(jobs.count(), 0)

    def test_get_create_job_view(self):
        """Test accessing the create job view with a GET request."""
        response = self.client.get(reverse("create_job"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "ssherlock_server/objects/add_object.html")
