""".Populate the current working database with a bunch of test objects."""

# pylint: disable=wrong-import-position, too-many-locals, missing-function-docstring, no-member

import sys
import os
import django

# Set up Django environment
sys.path.insert(1, "./ssherlock")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ssherlock.settings")
django.setup()

from ssherlock_server.models import (
    User,
    BastionHost,
    Credential,
    Job,
    LlmApi,
    TargetHost,
)


def populate_database():
    user1, _ = User.objects.get_or_create(email="user1@example.com")
    user2, _ = User.objects.get_or_create(email="user2@example.com")
    user3, _ = User.objects.get_or_create(email="user3@example.com")
    user4, _ = User.objects.get_or_create(email="user4@example.com")
    user5, _ = User.objects.get_or_create(email="user5@example.com")
    user6, _ = User.objects.get_or_create(email="user6@example.com")
    user7, _ = User.objects.get_or_create(email="user7@example.com")

    bastion1, _ = BastionHost.objects.get_or_create(
        hostname="bastion1.example.com", port=21, user=user1
    )
    bastion2, _ = BastionHost.objects.get_or_create(
        hostname="bastion2.example.com", port=22, user=user2
    )
    bastion3, _ = BastionHost.objects.get_or_create(
        hostname="bastion3.example.com", port=23, user=user3
    )
    bastion4, _ = BastionHost.objects.get_or_create(
        hostname="bastion4.example.com", port=24, user=user4
    )
    bastion5, _ = BastionHost.objects.get_or_create(
        hostname="bastion5.example.com", port=25, user=user5
    )
    bastion6, _ = BastionHost.objects.get_or_create(
        hostname="bastion6.example.com", port=26, user=user6
    )
    bastion7, _ = BastionHost.objects.get_or_create(
        hostname="bastion7.example.com", port=27, user=user7
    )

    credential1, _ = Credential.objects.get_or_create(
        credential_name="credential1",
        username="user1",
        password="pass1",
        user=user1,
    )
    credential2, _ = Credential.objects.get_or_create(
        credential_name="credential2",
        username="user2",
        password="pass2",
        user=user2,
    )
    credential3, _ = Credential.objects.get_or_create(
        credential_name="credential3",
        username="user3",
        password="pass3",
        user=user3,
    )
    credential4, _ = Credential.objects.get_or_create(
        credential_name="credential4",
        username="user4",
        password="pass4",
        user=user4,
    )
    credential5, _ = Credential.objects.get_or_create(
        credential_name="credential5",
        username="user5",
        password="pass5",
        user=user5,
    )
    credential6, _ = Credential.objects.get_or_create(
        credential_name="credential6",
        username="user6",
        password="pass6",
        user=user6,
    )
    credential7, _ = Credential.objects.get_or_create(
        credential_name="credential7",
        username="user7",
        password="pass7",
        user=user7,
    )

    llm_api1, _ = LlmApi.objects.get_or_create(
        base_url="https://api1.example.com", api_key="dummy_key1", user=user1
    )
    llm_api2, _ = LlmApi.objects.get_or_create(
        base_url="https://api2.example.com", api_key="dummy_key2", user=user2
    )
    llm_api3, _ = LlmApi.objects.get_or_create(
        base_url="https://api3.example.com", api_key="dummy_key3", user=user3
    )
    llm_api4, _ = LlmApi.objects.get_or_create(
        base_url="https://api4.example.com", api_key="dummy_key4", user=user4
    )
    llm_api5, _ = LlmApi.objects.get_or_create(
        base_url="https://api5.example.com", api_key="dummy_key5", user=user5
    )
    llm_api6, _ = LlmApi.objects.get_or_create(
        base_url="https://api6.example.com", api_key="dummy_key6", user=user6
    )
    llm_api7, _ = LlmApi.objects.get_or_create(
        base_url="https://api7.example.com", api_key="dummy_key7", user=user7
    )

    target_host1, _ = TargetHost.objects.get_or_create(
        hostname="target-host1.example.com", port=21, user=user1
    )
    target_host2, _ = TargetHost.objects.get_or_create(
        hostname="target-host2.example.com", port=22, user=user2
    )
    target_host3, _ = TargetHost.objects.get_or_create(
        hostname="target-host3.example.com", port=23, user=user3
    )
    target_host4, _ = TargetHost.objects.get_or_create(
        hostname="target-host4.example.com", port=24, user=user4
    )
    target_host5, _ = TargetHost.objects.get_or_create(
        hostname="target-host5.example.com", port=25, user=user5
    )
    target_host6, _ = TargetHost.objects.get_or_create(
        hostname="target-host6.example.com", port=26, user=user6
    )
    target_host7, _ = TargetHost.objects.get_or_create(
        hostname="target-host7.example.com", port=27, user=user7
    )

    job1, _ = Job.objects.get_or_create(
        user=user1,
        llm_api=llm_api1,
        bastion_host=bastion1,
        credentials_for_bastion_host=credential1,
        credentials_for_target_hosts=credential1,
        instructions="Instructions for job1",
        status="Canceled",
    )
    job1.target_hosts.add(target_host1)

    job2, _ = Job.objects.get_or_create(
        user=user2,
        llm_api=llm_api2,
        bastion_host=bastion2,
        credentials_for_bastion_host=credential2,
        credentials_for_target_hosts=credential2,
        instructions="Instructions for job2",
        status="Context exceeded",
    )
    job2.target_hosts.add(target_host2)

    job3, _ = Job.objects.get_or_create(
        user=user3,
        llm_api=llm_api3,
        bastion_host=bastion3,
        credentials_for_bastion_host=credential3,
        credentials_for_target_hosts=credential3,
        instructions="Instructions for job3",
        status="Completed",
    )
    job3.target_hosts.add(target_host3)

    job4, _ = Job.objects.get_or_create(
        user=user4,
        llm_api=llm_api4,
        bastion_host=bastion4,
        credentials_for_bastion_host=credential4,
        credentials_for_target_hosts=credential4,
        instructions="Instructions for job4",
        status="Failed",
    )
    job4.target_hosts.add(target_host4)

    job5, _ = Job.objects.get_or_create(
        user=user5,
        llm_api=llm_api5,
        bastion_host=bastion5,
        credentials_for_bastion_host=credential5,
        credentials_for_target_hosts=credential5,
        instructions="Instructions for job5",
        status="Pending",
    )
    job5.target_hosts.add(target_host5)

    job6, _ = Job.objects.get_or_create(
        user=user6,
        llm_api=llm_api6,
        bastion_host=bastion6,
        credentials_for_bastion_host=credential6,
        credentials_for_target_hosts=credential6,
        instructions="Instructions for job6",
        status="Pending",
    )
    job6.target_hosts.add(target_host6)

    job7, _ = Job.objects.get_or_create(
        user=user7,
        llm_api=llm_api7,
        bastion_host=bastion7,
        credentials_for_bastion_host=credential7,
        credentials_for_target_hosts=credential7,
        instructions="Instructions for job7",
        status="Running",
    )
    job7.target_hosts.add(target_host7)


if __name__ == "__main__":
    populate_database()
