"""All Django models for the SSHerlock server application."""

# pylint: disable=import-error, missing-class-docstring, invalid-str-returned

import uuid

from django.db import models


class User(models.Model):
    """Placeholder user model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.CharField(max_length=255)
    created_at = models.DateTimeField("date user was created", auto_now_add=True)

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email


class BastionHost(models.Model):
    """Defines bastion hosts for connecting through to target hosts."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(
        "date bastion host was created", auto_now_add=True, editable=False
    )
    hostname = models.CharField(max_length=253)
    port = models.IntegerField()

    class Meta:
        ordering = ["hostname"]

    def __str__(self):
        return self.hostname


class Credential(models.Model):
    """Defines username/password/key pairs for connecting to bastions and target hosts."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(
        "Date credential was created", auto_now_add=True, editable=False
    )
    credential_name = models.CharField("Name to give this credential", max_length=255)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    class Meta:
        ordering = ["credential_name"]

    def __str__(self):
        return self.credential_name


class LlmApi(models.Model):
    """Defines the APIs we will connect to for interacting with large language models."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(
        "date llm api was created", auto_now_add=True, editable=False
    )
    base_url = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255)

    class Meta:
        ordering = ["base_url"]

    def __str__(self):
        return self.base_url


class TargetHost(models.Model):
    """Defines a host that the LLM will run commands against."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(
        "Date target host was created", auto_now_add=True, editable=False
    )
    hostname = models.CharField(max_length=253)
    port = models.IntegerField()

    class Meta:
        ordering = ["hostname"]

    def __str__(self):
        return self.hostname


class Job(models.Model):
    """
    Defines a job in which the LLM runs against a target server.

    The LLM must complete a set of instructions before the job is complete.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(
        "Date job was created", auto_now_add=True, editable=False
    )
    started_at = models.DateTimeField(
        "Date job was started", blank=True, null=True, editable=False
    )
    completed_at = models.DateTimeField(
        "Date job was completed", blank=True, null=True, editable=False
    )
    stopped_at = models.DateTimeField(
        "Date job was stopped", blank=True, null=True, editable=False
    )
    duration = models.DurationField(
        "Amount of time job took to complete", blank=True, null=True, editable=False
    )
    STATUS_CHOICES = [
        ("CA", "CANCELED"),
        ("CE", "CONTEXT_EXCEEDED"),
        ("CO", "COMPLETED"),
        ("FA", "FAILED"),
        ("PE", "PENDING"),
        ("RU", "RUNNING"),
    ]
    status = models.CharField(
        "Current status of job",
        max_length=32,
        choices=STATUS_CHOICES,
        default="PENDING",
        editable=False
    )
    llm_api = models.ForeignKey(LlmApi, on_delete=models.SET_NULL, null=True)
    bastion_host = models.ForeignKey(
        BastionHost, on_delete=models.SET_NULL, blank=True, null=True
    )
    credentials_for_bastion_host = models.ForeignKey(
        Credential,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="bastion_hosts",
    )
    target_hosts = models.ManyToManyField(TargetHost)
    credentials_for_target_hosts = models.ForeignKey(
        Credential, on_delete=models.SET_NULL, null=True, related_name="target_hosts"
    )
    instructions = models.TextField()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return str(self.id)

    def dict(self) -> dict[any]:
        """Return relevant object data as a dict."""
        return {
            "id": str(self.id),
            "llm_api_baseurl": getattr(self.llm_api, "base_url", None),
            "llm_api_api_key": getattr(self.llm_api, "api_key", None),
            "bastion_host_hostname": getattr(self.bastion_host, "hostname", None),
            "bastion_host_port": getattr(self.bastion_host, "port", None),
            "credentials_for_bastion_host_username": getattr(
                self.credentials_for_bastion_host, "username", None
            ),
            "credentials_for_bastion_host_password": getattr(
                self.credentials_for_bastion_host, "password", None
            ),
            "target_host_hostname": getattr(self.target_hosts.first(), "hostname", None),
            "target_host_port": getattr(self.target_hosts.first(), "port", None),
            "credentials_for_target_hosts_username": getattr(
                self.credentials_for_target_hosts, "username", None
            ),
            "credentials_for_target_hosts_password": getattr(
                self.credentials_for_target_hosts, "password", None
            ),
            "instructions": self.instructions,
        }
