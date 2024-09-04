from django.test import TestCase
from ssherlock_server.models import User, BastionHost, Credential, TargetHost, LlmApi, Job
import datetime
import uuid


class TestUser(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(email="user1@example.com")
        self.user2 = User.objects.create(email="user2@example.com")

    def test_creation(self):
        user = User.objects.get(email="user1@example.com")
        self.assertEqual(user.email, "user1@example.com")
        self.assertIsInstance(user.id, uuid.UUID)

    def test_str_method(self):
        self.assertEqual(str(self.user1), "user1@example.com")

    def test_ordering(self):
        users = User.objects.all()
        self.assertEqual(users[0], self.user1)
        self.assertEqual(users[1], self.user2)


class TestBastionHost(TestCase):
    """Test creating, reading, editing, and deleting bastion host objects."""
    def setUp(self):
        self.user = User.objects.create(email="user@example.com")
        self.bastion1 = BastionHost.objects.create(
            user=self.user, hostname="bastion1.example.com", port=22
        )
        self.bastion2 = BastionHost.objects.create(
            user=self.user, hostname="bastion2.example.com", port=2222
        )
        self.bastion3 = BastionHost.objects.create(
            user=self.user, hostname="bastion3.example.com", port=230
        )

    def test_reading_attributes(self):
        bastion = BastionHost.objects.get(hostname="bastion1.example.com")

        self.assertEqual(bastion.hostname, "bastion1.example.com")
        self.assertEqual(bastion.port, 22)

        self.assertIsInstance(bastion.port, int)
        self.assertIsInstance(bastion.id, uuid.UUID)
        self.assertIsInstance(bastion.created_at, datetime.datetime)

    def test_editing_attributes(self):
        bastion = BastionHost.objects.get(hostname="bastion2.example.com")

        bastion.hostname = "bastion2.edited.example.com"
        bastion.port = 224

        self.assertEqual(bastion.hostname, "bastion2.edited.example.com")
        self.assertEqual(bastion.port, 224)

    def test_deletion(self):
        bastion = BastionHost.objects.get(hostname="bastion3.example.com")
        bastion.delete()

        self.assertEqual(len(BastionHost.objects.all()), 2)

    def test_str_method(self):
        self.assertEqual(str(self.bastion1), "bastion1.example.com")

    def test_ordering(self):
        bastions = BastionHost.objects.all()
        self.assertEqual(bastions[0], self.bastion1)
        self.assertEqual(bastions[1], self.bastion2)
        self.assertEqual(bastions[2], self.bastion3)


class TestCredential(TestCase):
    """Test creating, reading, editing, and deleting credential objects."""
    def setUp(self):
        self.user = User.objects.create(email="user@example.com")
        self.credential1 = Credential.objects.create(
            user=self.user, credential_name="Credential 1", username="user1", password="pass1"
        )
        self.credential2 = Credential.objects.create(
            user=self.user, credential_name="Credential 2", username="user2", password="pass2"
        )

    def test_reading_attributes(self):
        credential = Credential.objects.get(credential_name="Credential 1")

        self.assertEqual(credential.credential_name, "Credential 1")
        self.assertEqual(credential.username, "user1")

        self.assertIsInstance(credential.username, str)
        self.assertIsInstance(credential.credential_name, str)
        self.assertIsInstance(credential.id, uuid.UUID)
        self.assertIsInstance(credential.created_at, datetime.datetime)

    def test_editing_attributes(self):
        credential = Credential.objects.get(credential_name="Credential 2")

        credential.credential_name = "Credential 2 Edited"
        credential.username = "user2_edited"

        self.assertEqual(credential.credential_name, "Credential 2 Edited")
        self.assertEqual(credential.username, "user2_edited")

    def test_deletion(self):
        credential = Credential.objects.get(credential_name="Credential 1")
        credential.delete()

        self.assertEqual(len(Credential.objects.all()), 1)

    def test_str_method(self):
        self.assertEqual(str(self.credential1), "Credential 1")

    def test_ordering(self):
        credentials = Credential.objects.all()
        self.assertEqual(credentials[0], self.credential1)
        self.assertEqual(credentials[1], self.credential2)


class TestTargetHost(TestCase):
    """Test creating, reading, editing, and deleting target host objects."""
    def setUp(self):
        self.user = User.objects.create(email="user@example.com")
        self.target_host1 = TargetHost.objects.create(
            user=self.user, hostname="target1.example.com", port=22
        )
        self.target_host2 = TargetHost.objects.create(
            user=self.user, hostname="1.2.3.4", port=2222
        )

    def test_reading_attributes(self):
        target_host = TargetHost.objects.get(hostname="target1.example.com")

        self.assertEqual(target_host.hostname, "target1.example.com")
        self.assertEqual(target_host.port, 22)

        self.assertIsInstance(target_host.hostname, str)
        self.assertIsInstance(target_host.id, uuid.UUID)
        self.assertIsInstance(target_host.created_at, datetime.datetime)

    def test_editing_attributes(self):
        target_host = TargetHost.objects.get(hostname="1.2.3.4")

        target_host.hostname = "3.4.5.6"
        target_host.port = 224

        self.assertEqual(target_host.hostname, "3.4.5.6")
        self.assertEqual(target_host.port, 224)

    def test_deletion(self):
        target_host = TargetHost.objects.get(hostname="target1.example.com")
        target_host.delete()

        self.assertEqual(len(TargetHost.objects.all()), 1)

    def test_str_method(self):
        self.assertEqual(str(self.target_host1), "target1.example.com")

    def test_ordering(self):
        target_hosts = TargetHost.objects.all()
        # Reverse ordering because "1.2.3.4" is before "target1" alphabetically.
        self.assertEqual(target_hosts[1], self.target_host1)
        self.assertEqual(target_hosts[0], self.target_host2)


class TestLlmApi(TestCase):
    """Test creating, reading, editing, and deleting LLM API objects."""
    def setUp(self):
        self.user = User.objects.create(email="user@example.com")
        self.llm_api1 = LlmApi.objects.create(
            user=self.user, base_url="https://api1.example.com", api_key="key1"
        )
        self.llm_api2 = LlmApi.objects.create(
            user=self.user, base_url="https://api2.example.com", api_key="key2"
        )

    def test_reading_attributes(self):
        llm_api = LlmApi.objects.get(base_url="https://api1.example.com")

        self.assertEqual(llm_api.base_url, "https://api1.example.com")
        self.assertEqual(llm_api.api_key, "key1")

        self.assertIsInstance(llm_api.base_url, str)
        self.assertIsInstance(llm_api.api_key, str)
        self.assertIsInstance(llm_api.id, uuid.UUID)
        self.assertIsInstance(llm_api.created_at, datetime.datetime)

    def test_editing_attributes(self):
        llm_api = LlmApi.objects.get(base_url="https://api2.example.com")

        llm_api.base_url = "https://api2.edited.example.com"
        llm_api.api_key = "key2_edited"

        self.assertEqual(llm_api.base_url, "https://api2.edited.example.com")
        self.assertEqual(llm_api.api_key, "key2_edited")

    def test_deletion(self):
        llm_api = LlmApi.objects.get(base_url="https://api1.example.com")
        llm_api.delete()

        self.assertEqual(len(LlmApi.objects.all()), 1)

    def test_str_method(self):
        self.assertEqual(str(self.llm_api1), "https://api1.example.com")

    def test_ordering(self):
        llm_apis = LlmApi.objects.all()
        self.assertEqual(llm_apis[0], self.llm_api1)
        self.assertEqual(llm_apis[1], self.llm_api2)


class TestJob(TestCase):
    """Test creating, reading, editing, and deleting Job objects."""
    def setUp(self):
        self.user = User.objects.create(email="user@example.com")
        self.llm_api = LlmApi.objects.create(
            user=self.user, base_url="https://api.example.com", api_key="key"
        )
        self.bastion_host = BastionHost.objects.create(
            user=self.user, hostname="bastion.example.com", port=22
        )
        self.credential = Credential.objects.create(
            user=self.user, credential_name="Credential", username="user", password="pass"
        )
        self.target_host = TargetHost.objects.create(
            user=self.user, hostname="target.example.com", port=22
        )
        self.job1 = Job.objects.create(
            user=self.user,
            llm_api=self.llm_api,
            bastion_host=self.bastion_host,
            credentials_for_bastion_host=self.credential,
            credentials_for_target_hosts=self.credential,
            instructions="Run diagnostics"
        )
        # Directly setting a ManyToManyField isn't allowed so use add here.
        self.job1.target_hosts.add(self.target_host)

    def test_reading_attributes(self):
        job = Job.objects.get(id=self.job1.id)

        self.assertEqual(job.instructions, "Run diagnostics")
        self.assertEqual(job.status, "PENDING")
        self.assertEqual(job.llm_api, self.llm_api)
        self.assertEqual(job.bastion_host, self.bastion_host)
        self.assertEqual(job.credentials_for_bastion_host, self.credential)
        self.assertEqual(job.credentials_for_target_hosts, self.credential)

        self.assertIsInstance(job.status, str)
        self.assertIsInstance(job.instructions, str)

        self.assertIsInstance(job.llm_api, LlmApi)
        self.assertIsInstance(job.bastion_host, BastionHost)
        self.assertIsInstance(job.credentials_for_bastion_host, Credential)
        self.assertIsInstance(job.credentials_for_target_hosts, Credential)

        self.assertIsInstance(job.id, uuid.UUID)
        self.assertIsInstance(job.created_at, datetime.datetime)

    def test_editing_attributes(self):
        job = Job.objects.get(id=self.job1.id)

        job.instructions = "Run security scan"
        job.status = "RUNNING"
        job.save()

        self.assertEqual(job.instructions, "Run security scan")
        self.assertEqual(job.status, "RUNNING")

    def test_deletion(self):
        job = Job.objects.get(id=self.job1.id)
        job.delete()

        self.assertEqual(len(Job.objects.all()), 0)

    def test_str_method(self):
        self.assertEqual(str(self.job1), str(self.job1.id))
