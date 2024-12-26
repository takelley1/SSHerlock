"""Populate the current working database with a bunch of test objects."""

# pylint: disable=wrong-import-position, too-many-locals, missing-function-docstring, no-member

import sys
import os
import django
import random as rand

# Set up Django environment
sys.path.insert(1, "./ssherlock")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ssherlock.settings")
django.setup()

from django.contrib.auth.models import User

from ssherlock_server.models import (
    BastionHost,
    Credential,
    Job,
    LlmApi,
    TargetHost,
)


def populate_database():
    for i in range(20, 30):
        user = User.objects.create_user(f"user{i}", f"user{i}@example.com", "password")
        print(f"Created user{i}")

        for p in range(1, 100):
            bastion_port = rand.randint(20, 65536)

            bastion, _ = BastionHost.objects.get_or_create(
                hostname=f"bastion{p}.example.com", port=bastion_port, user=user
            )
            print(f"Created bastion{p}")

            credential, _ = Credential.objects.get_or_create(
                credential_name=f"credential{p}",
                username=f"user{i}",
                password=f"pass{p}",
                user=user,
            )
            print(f"Created credential{p}")

            llm_api, _ = LlmApi.objects.get_or_create(
                base_url=f"https://api{p}.example.com",
                api_key=f"dummy_key{p}",
                user=user,
            )
            print(f"Created llm_api{i}")

            target_host, _ = TargetHost.objects.get_or_create(
                hostname=f"target-host{p}.example.com", port=bastion_port, user=user
            )
            print(f"Created target_host{i}")

            job, _ = Job.objects.get_or_create(
                user=user,
                llm_api=llm_api,
                bastion_host=bastion,
                credentials_for_bastion_host=credential,
                credentials_for_target_hosts=credential,
                instructions=f"Instructions for job{i}",
                status="Canceled",
            )
            job.target_hosts.add(target_host)
            print(f"Created job{i}")


if __name__ == "__main__":
    populate_database()
