from django.db import models


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published")


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)


class User(models.Model):
    email = models.CharField(max_length=255)
    creation_time = models.DateTimeField("date user was created")

    def __str__(self):
        return self.email


class Credential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    creation_time = models.DateTimeField("date credential was created")
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    # sudo_username
    # sudo_password
    def __str__(self):
        return self.username


class TargetServer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    creation_time = models.DateTimeField("date target server was created")
    # https://stackoverflow.com/questions/8724954/what-is-the-maximum-number-of-characters-for-a-host-name-in-unix
    hostname = models.CharField(max_length=253)

    def __str__(self):
        return self.hostname


class LlmApi(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    creation_time = models.DateTimeField("date llm api was created")
    base_url = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255)

    def __str__(self):
        return self.base_url
