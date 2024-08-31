from django.test import TestCase
from ssherlock_server.models import User, BastionHost, Credential
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
    def setUp(self):
        self.user = User.objects.create(email="user@example.com")
        self.bastion1 = BastionHost.objects.create(
            user=self.user, hostname="bastion1.example.com", port=22
        )
        self.bastion2 = BastionHost.objects.create(
            user=self.user, hostname="bastion2.example.com", port=2222
        )

    def test_creation(self):
        bastion = BastionHost.objects.get(hostname="bastion1.example.com")
        self.assertEqual(bastion.hostname, "bastion1.example.com")
        self.assertEqual(bastion.port, 22)
        self.assertIsInstance(bastion.id, uuid.UUID)

    def test_str_method(self):
        self.assertEqual(str(self.bastion1), "bastion1.example.com")

    def test_ordering(self):
        bastions = BastionHost.objects.all()
        self.assertEqual(bastions[0], self.bastion1)
        self.assertEqual(bastions[1], self.bastion2)


class TestCredential(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="user@example.com")
        self.credential1 = Credential.objects.create(
            user=self.user, credential_name="Credential1", username="user1", password="password123"
        )
        self.credential2 = Credential.objects.create(
            user=self.user, credential_name="Credential2", username="admin", password="admin123"
        )

    def test_creation(self):
        credential = Credential.objects.get(credential_name="Credential1")
        self.assertEqual(credential.username, "user1")
        self.assertEqual(credential.password, "password123")
        self.assertIsInstance(credential.id, uuid.UUID)

    def test_str_method(self):
        self.assertEqual(str(self.credential1), "Credential1")

    def test_ordering(self):
        credentials = Credential.objects.all()
        self.assertEqual(credentials[0], self.credential1)
        self.assertEqual(credentials[1], self.credential2)
