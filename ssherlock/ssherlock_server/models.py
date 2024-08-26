from django.db import models
from django.conf import settings


class User(models.Model):
    email = models.CharField(max_length=255)
    creation_time = models.DateTimeField("date user was created", auto_now_add=True)

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email


class BastionServer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    creation_time = models.DateTimeField(
        "date bastion server was created", auto_now_add=True
    )
    hostname = models.CharField(max_length=253)

    class Meta:
        ordering = ["hostname"]

    def __str__(self):
        return self.hostname


class Credential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    creation_time = models.DateTimeField(
        "Date credential was created", auto_now_add=True
    )
    credential_name = models.CharField("Name to give this credential", max_length=255)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    class Meta:
        ordering = ["credential_name"]

    def __str__(self):
        return self.credential_name


class LlmApi(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    creation_time = models.DateTimeField("date llm api was created", auto_now_add=True)
    base_url = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255)

    class Meta:
        ordering = ["base_url"]

    def __str__(self):
        return self.base_url


class TargetServer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    creation_time = models.DateTimeField(
        "date target server was created", auto_now_add=True
    )
    hostname = models.CharField(max_length=253)

    class Meta:
        ordering = ["hostname"]

    def __str__(self):
        return self.hostname


class Job(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    start_time = models.DateTimeField("date job was started", auto_now_add=True)
    stop_time = models.DateTimeField("date job was stopped", blank=True, null=True)
    completion_time = models.DateTimeField(
        "date job was completed", blank=True, null=True
    )
    duration = models.DurationField(
        "amount of time job took to complete", blank=True, null=True
    )

    llm_api = models.ForeignKey(LlmApi, on_delete=models.SET_NULL, null=True)

    bastion_server = models.ForeignKey(
        BastionServer, on_delete=models.SET_NULL, blank=True, null=True
    )
    credentials_for_bastion = models.ForeignKey(
        Credential,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="bastion_servers",
    )

    target_servers = models.ManyToManyField(TargetServer)
    credentials_for_target_servers = models.ForeignKey(
        Credential, on_delete=models.SET_NULL, null=True, related_name="target_servers"
    )

    instructions = models.TextField()

    output_path = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return str(self.id)
