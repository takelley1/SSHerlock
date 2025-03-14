"""Test the functions in the runner."""

# pylint: disable=import-error, redefined-outer-name, wrong-import-position

import sys
import json
import os

from unittest.mock import MagicMock
from unittest.mock import patch
from unittest import TestCase

import openai
import requests
import pytest

os.environ["RUNNER_NUMBER"] = "1"
sys.path.insert(1, "../")
from ssherlock_runner import (
    Runner,
    count_tokens,
    get_runner_number,
    is_llm_done,
    is_string_too_long,
    main,
    request_job,
    run_job,
    strip_eot_from_string,
    update_conversation,
    update_job_status,
)


SSHERLOCK_SERVER_DOMAIN = "localhost:8000"
SSHERLOCK_SERVER_PROTOCOL = "http"
SSHERLOCK_SERVER_RUNNER_TOKEN = "myprivatekey"


@pytest.fixture
def job():
    """Fixture to set up a Runner object."""
    return Runner(
        job_id="1234567890abcdef",
        llm_api_base_url="api1.example.com",
        initial_prompt="Initial prompt example message.",
        target_host_hostname="target1.example.com",
        credentials_for_target_hosts_username="user1",
        log_level="CRITICAL",
        model_context_size=16,
        credentials_for_target_hosts_keyfile="/path/to/keyfile",
        credentials_for_target_hosts_password="pass123",
    )


def test_strip_eot_from_string():
    """Ensure the end of token footer is stripped from strings correctly."""
    assert strip_eot_from_string("Hello, World!<|eot_id|>") == "Hello, World!"
    assert strip_eot_from_string("Hello, World!") == "Hello, World!"


def test_is_string_too_long():
    """Ensure is_string_too_long returns the correct bool for a given input."""
    assert is_string_too_long("a" * 1001) is True
    assert is_string_too_long("a" * 1000) is False
    assert is_string_too_long("a" * 999) is False
    assert is_string_too_long("a" * 501, threshold=500) is True
    assert is_string_too_long("a" * 499, threshold=500) is False


def test_count_tokens():
    """Ensure tokens get counted correctly."""
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "What is the capital of Japan?"},
        {"role": "assistant", "content": "Tokyo"},
    ]
    assert count_tokens(messages) == 15
    messages = [
        {"role": "system", "content": ""},
        {"role": "user", "content": ""},
        {"role": "assistant", "content": ""},
    ]
    assert count_tokens(messages) == 1


def test_context_size_warning_check(job):
    """Ensure we get warned properly when the context is about to be exceeded."""
    messages = [
        {"role": "system", "content": "You're a helpful AI assistant."},
        {"role": "user", "content": "What is the capital of Japan?"},
        {"role": "assistant", "content": "Tokyo"},
    ]
    assert job.context_size_warning_check(messages, threshold=0.85) is True

    # If the model context size isn't set, the function should return false.
    job = Runner(
        job_id="123",
        llm_api_base_url="test",
        initial_prompt="test",
        target_host_hostname="test",
        credentials_for_target_hosts_username="test",
        model_context_size=0,
    )
    assert job.context_size_warning_check(messages, threshold=0.85) is False

    job = Runner(
        job_id="123",
        llm_api_base_url="test",
        initial_prompt="test",
        target_host_hostname="test",
        credentials_for_target_hosts_username="test",
        model_context_size=10000,
    )
    assert job.context_size_warning_check(messages, threshold=0.85) is False


def test_is_llm_done():
    """Ensure we can detect when the LLM is done."""
    assert is_llm_done("DONE") is True
    assert is_llm_done("Not done") is False
    assert is_llm_done("done") is False


def test_initialize_messages(job):
    """Ensure the initial prompt gets added properly."""
    messages = job.initialize_messages()
    assert len(messages) == 2
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Initial prompt example message."


def test_setup_ssh_connection_params_with_keyfile():
    """Ensure the SSH connect args use a keyfile when one is passed."""
    job = Runner(
        job_id="123",
        llm_api_base_url="test",
        initial_prompt="test",
        target_host_hostname="test",
        credentials_for_target_hosts_username="test",
        credentials_for_target_hosts_keyfile="/path/to/keyfile",
    )
    connect_args = job.setup_ssh_connection_params()
    assert connect_args["key_filename"] == "/path/to/keyfile"


def test_setup_ssh_connection_params_with_password():
    """Ensure the SSH connect args use a password when one is passed."""
    job = Runner(
        job_id="123",
        llm_api_base_url="test",
        initial_prompt="test",
        target_host_hostname="test",
        credentials_for_target_hosts_username="test",
        credentials_for_target_hosts_password="pass123",
    )
    connect_args = job.setup_ssh_connection_params()
    print(connect_args)
    assert connect_args["password"] == "pass123"


def test_query_llm(job):
    """Ensure querying the LLM returns expected results."""
    prompt = [
        {"role": "system", "content": "You're a helpful AI assistant."},
        {"role": "user", "content": "What is the capital of Japan?"},
    ]

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Tokyo<|eot_id|>"
    mock_client.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client):
        response = job.query_llm(prompt)
        assert response == "Tokyo"


def test_can_llm_be_reached_success(job):
    """Ensure the correct bool is returned when we check the reachability of the LLM and succeed."""
    with patch.object(job, "query_llm", return_value="GOOD"):
        assert job.can_llm_be_reached() is True


def test_can_llm_be_reached_failure(job):
    """Ensure the correct bool is returned when we check the reachability of the LLM and fail."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    with patch.object(
        job,
        "query_llm",
        side_effect=openai.InternalServerError(
            response=mock_response, body="Error", message="Error"
        ),
    ):
        assert job.can_llm_be_reached() is False


def test_wait_for_llm_to_become_available_success(job):
    """Ensure waiting for LLM to be available after multiple failed attempts works correctly."""

    with patch.object(job, "can_llm_be_reached", side_effect=[False, False, True]):
        # Mock sleep to speed up the test.
        with patch("time.sleep", return_value=None):
            job.wait_for_llm_to_become_available()


def test_wait_for_llm_to_become_available_timeout(job):
    """Ensure waiting for the LLM to become available and timing out throws an error."""

    with patch.object(job, "can_llm_be_reached", return_value=False):
        # Mock sleep to speed up the test.
        with patch("time.sleep", return_value=None):
            with pytest.raises(
                RuntimeError,
                match="Timed out waiting for LLM server to become available!",
            ):
                job.wait_for_llm_to_become_available()


def test_summarize_string(job):
    """Mock the OpernAI API to test string summarization function."""
    string_to_summarize = "This is a long text that needs to be summarized."

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Summarized text"
    mock_client.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client):
        summary = job.summarize_string(string_to_summarize)
        assert summary == "Summarized text"


def test_run_ssh_cmd_with_sudo(job):
    """Ensure stdout and stderr get combined correctly in mocked SSH command with sudo."""
    job.credentials_for_target_hosts_sudo_password = "sudo_password"

    mock_connection = MagicMock()
    mock_result = MagicMock()
    mock_result.stdout.strip.return_value = "Command output"
    mock_result.stderr.strip.return_value = "Error output"
    mock_connection.sudo.return_value = mock_result

    command_output = job.run_ssh_cmd(mock_connection, "echo Hello")
    assert command_output == "Command outputError output"


def test_run_ssh_cmd_without_sudo(job):
    """Ensure stdout and stderr get combined correctly in mocked SSH command without sudo."""
    job.target_host_user_sudo_password = ""

    mock_connection = MagicMock()
    mock_result = MagicMock()
    mock_result.stdout.strip.return_value = "Command output"
    mock_result.stderr.strip.return_value = "Error output"
    mock_connection.run.return_value = mock_result

    command_output = job.run_ssh_cmd(mock_connection, "echo Hello")
    assert command_output == "Command outputError output"


# @patch("ssherlock_runner.log.debug")
# @patch("ssherlock_runner.log.error")
# @patch("ssherlock_runner.update_job_status")
# def test_run_ssh_cmd_failure(mock_update_status, mock_log_error, mock_log_debug, runner):
#     """Test run_ssh_cmd method when the SSH command fails."""
#     mock_connection = MagicMock(spec=fabric.Connection)
#     # Simulate an exception being raised during the SSH command execution
#     mock_connection.sudo.side_effect = Exception("Command execution failed")

#     with TestCase.assertRaises(TestCase(), Exception) as context:
#         job.run_ssh_cmd(mock_connection, "ls -la")

#     assert str(context.exception) == "Command execution failed"
#     mock_log_error.assert_called_once_with("SSH command failed: %s", "Command execution failed")
#     mock_update_status.assert_called_once_with("1234567890abcdef", "Failed")


def test_handle_ssh_command_no_summarization(job):
    """Ensure running an SSH command works correctly without output summarization."""
    mock_ssh = MagicMock()
    mock_llm_reply = "ls -1"
    mock_ssh_reply = "dir1 dir2 dir3 file1.txt file2.txt"

    with patch.object(job, "run_ssh_cmd", return_value=mock_ssh_reply):
        response = job.handle_ssh_command(mock_ssh, mock_llm_reply)
        assert response == mock_ssh_reply


def test_handle_ssh_command_with_summarization(job):
    """Ensure running an SSH command works correctly with output summarization."""
    mock_ssh = MagicMock()
    mock_llm_reply = "ls -1"
    mock_ssh_reply = "dir1 dir2 dir3 file1.txt file2.txt"
    summarized_output = "A list of directories and files."

    # Patch both the run_ssh_cmd method and the is_string_too_long method.
    with patch.object(job, "run_ssh_cmd", return_value=mock_ssh_reply), patch(
        "ssherlock_runner.is_string_too_long", return_value=True
    ), patch.object(job, "summarize_string", return_value=summarized_output):

        # When the string is too long, it should be summarized.
        response = job.handle_ssh_command(mock_ssh, mock_llm_reply)
        assert response == summarized_output


def test_update_job_status_success():
    """Ensure job status is updated successfully."""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        update_job_status("job123", "Completed")
        mock_post.assert_called_once_with(
            f"{SSHERLOCK_SERVER_PROTOCOL}://{SSHERLOCK_SERVER_DOMAIN}/update_job_status/job123",
            headers={
                "Authorization": f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}",
                "Content-Type": "application/json",
            },
            data=json.dumps({"status": "Completed"}),
            timeout=10,
        )


def test_update_job_status_failure():
    """Ensure proper logging on failure to update job status."""
    with patch("requests.post") as mock_post, patch(
        "ssherlock_runner.log.error"
    ) as mock_log_error:
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.content = b"Internal Server Error"
        mock_post.return_value = mock_response

        update_job_status("job123", "Failed")
        mock_log_error.assert_called_once_with(
            "Failed to update job %s status to %s. Status code: %d. Output: %s",
            "job123",
            "Failed",
            500,
            b"Internal Server Error",
        )


def test_update_job_status_exception():
    """Ensure proper logging on exception during job status update."""
    with patch("requests.post", side_effect=Exception("Connection error")) as _, patch(
        "ssherlock_runner.log.error"
    ) as mock_log_error:

        update_job_status("job123", "Failed")

        mock_log_error.assert_called_once_with(
            "Error updating job status for job %s: %s", "job123", "Connection error"
        )


def test_run_job():
    """Ensure run_job updates statuses and runs correctly."""
    job_data = {
        "id": "job123",
        "llm_api_baseurl": "http://api.example.com",
        "instructions": "Run this job",
        "target_host_hostname": "localhost",
        "credentials_for_target_hosts_username": "user",
        "credentials_for_target_hosts_password": "password",
        "llm_api_api_key": "api_key",
        "bastion_host_hostname": "bastion",
        "credentials_for_bastion_host_username": "bastion_user",
        "credentials_for_bastion_host_password": "bastion_pass",
    }

    with patch("ssherlock_runner.update_job_status") as _, patch(
        "ssherlock_runner.Runner"
    ) as mock_runner:

        mock_runner_instance = mock_runner.return_value
        run_job(job_data)
        mock_runner_instance.run.assert_called_once()


def test_request_job_success():
    """Ensure get_next_job fetches job data successfully."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "job123"}
        mock_get.return_value = mock_response

        job_data = request_job()
        assert job_data == {"id": "job123"}


def test_request_job_failure():
    """Ensure get_next_job handles network errors gracefully."""
    with patch(
        "requests.get", side_effect=requests.RequestException("Network error")
    ) as _, patch("ssherlock_runner.log.error") as mock_log_error:

        result = request_job()
        assert result is None

        # Verify that an error was logged with the correct format.
        mock_log_error.assert_called_once()
        args, _ = mock_log_error.call_args
        assert args[0] == "Error fetching job: %s"
        assert str(args[1]) == "Network error"


@patch("ssherlock_runner.Runner.wait_for_llm_to_become_available")
@patch("ssherlock_runner.Runner.can_target_server_be_reached", return_value=True)
def test_initialize_success(mock_can_reach, mock_wait_llm, job):
    """Test initialize method when the target server can be reached."""
    job.initialize()
    mock_can_reach.assert_called_once()
    mock_wait_llm.assert_called_once()


@patch("ssherlock_runner.log.critical")
@patch("ssherlock_runner.Runner.wait_for_llm_to_become_available")
@patch("ssherlock_runner.Runner.can_target_server_be_reached", return_value=False)
def test_initialize_failure(mock_log_critical, mock_wait_llm, mock_can_reach, job):
    """Test initialize method when the target server cannot be reached."""
    with TestCase.assertRaises(TestCase(), RuntimeError):
        job.initialize()

    mock_can_reach.assert_called_once()
    mock_log_critical.assert_called_once()
    mock_wait_llm.assert_not_called()


@patch("ssherlock_runner.log.warning")
@patch("ssherlock_runner.log.error")
@patch("ssherlock_runner.update_job_status")
@patch("ssherlock_runner.fabric.Connection")
def test_can_target_server_be_reached_success(
    mock_connection, mock_update_status, mock_log_error, mock_log_warning, job
):
    """Test can_target_server_be_reached method when the server is reachable."""
    job.setup_ssh_connection_params = MagicMock(return_value={"key": "value"})

    # Mock the run method of fabric.Connection to simulate successful command execution
    mock_connection.return_value.__enter__.return_value.run = MagicMock()

    result = job.can_target_server_be_reached()

    assert result is True
    mock_log_warning.assert_called_once_with("Checking target server reachability...")
    mock_log_error.assert_not_called()
    mock_update_status.assert_not_called()


@patch("ssherlock_runner.log.warning")
@patch("ssherlock_runner.log.error")
@patch("ssherlock_runner.update_job_status")
@patch("ssherlock_runner.fabric.Connection")
def test_can_target_server_be_reached_failure(
    mock_connection, mock_update_status, mock_log_error, mock_log_warning, job
):
    """Test can_target_server_be_reached method when the server is not reachable."""
    job.setup_ssh_connection_params = MagicMock(return_value={"key": "value"})

    # Simulate an exception being raised during the SSH connection attempt
    mock_connection.side_effect = Exception("Connection failed")

    result = job.can_target_server_be_reached()

    assert result is False
    mock_log_warning.assert_called_once_with("Checking target server reachability...")
    mock_log_error.assert_called_once_with(
        "Failed to reach the target server: %s", str(Exception("Connection failed"))
    )
    mock_update_status.assert_called_once_with("1234567890abcdef", "Failed")


@patch("ssherlock_runner.requests.get")
@patch("ssherlock_runner.log.error")
def test_is_job_canceled_success(mock_log_error, mock_requests_get, job):
    """Test is_job_canceled method when job status is 'Canceled'."""

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"status": "Canceled"}
    mock_requests_get.return_value = mock_response

    result = job.is_job_canceled()

    assert result is True
    mock_log_error.assert_not_called()


@patch("ssherlock_runner.requests.get")
@patch("ssherlock_runner.log.error")
def test_is_job_canceled_not_canceled(mock_log_error, mock_requests_get, job):
    """Test is_job_canceled method when job status is not 'Canceled'."""

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"status": "Running"}
    mock_requests_get.return_value = mock_response

    result = job.is_job_canceled()

    assert result is False
    mock_log_error.assert_not_called()


@patch("ssherlock_runner.requests.get")
@patch("ssherlock_runner.log.error")
def test_is_job_canceled_failure(mock_log_error, mock_requests_get, job):
    """Test is_job_canceled method when an exception occurs."""

    # Simulate a RequestException being raised
    mock_requests_get.side_effect = requests.RequestException("Network error")

    result = job.is_job_canceled()

    assert result is False
    mock_log_error.assert_called_once_with(
        "Error checking job status: %s", "Network error"
    )


@patch("ssherlock_runner.fabric.Connection")
@patch("ssherlock_runner.Runner.query_llm")
@patch("ssherlock_runner.update_job_status")
def test_process_interaction_with_exception(
    mock_update_job_status, mock_query_llm, mock_fabric_connection, job
):
    """
    Test the process_interaction_loop method to ensure it handles exceptions during SSH command execution.

    Mocks:
        - query_llm: Simulates LLM responses.
        - fabric.Connection: Mocks the SSH connection behavior to raise an exception.
        - update_job_status: Verifies that job status updates are called appropriately.

    Args:
        mock_update_job_status (MagicMock): Mock for updating job status.
        mock_query_llm (MagicMock): Mock for querying the LLM.
        mock_fabric_connection (MagicMock): Mock for fabric.Connection.
        job: The job instance being tested.

    Asserts:
        - Ensures the exception is raised and caught as expected.
        - Verifies the job status is updated to "Failed".
    """
    mock_query_llm.side_effect = ["command1"]

    # Mock SSH connection behavior with an exception
    mock_ssh_connection = MagicMock()
    mock_ssh_connection.run.side_effect = Exception("SSH error")
    mock_fabric_connection.return_value.__enter__.return_value = mock_ssh_connection

    # Initialize messages and connect_args
    messages = job.initialize_messages()
    connect_args = job.setup_ssh_connection_params()

    # Run the process_interaction_loop and expect it to handle the exception
    with pytest.raises(Exception) as excinfo:
        job.process_interaction_loop(messages, connect_args)
    assert str(excinfo.value) == "SSH error"

    # Assertions
    mock_update_job_status.assert_any_call(job.job_id, "Running")
    mock_update_job_status.assert_any_call(job.job_id, "Failed")


@patch("ssherlock_runner.fabric.Connection")
@patch("ssherlock_runner.Runner.query_llm")
@patch("ssherlock_runner.update_job_status")
def test_process_interaction_job_canceled(
    mock_update_job_status, mock_query_llm, mock_fabric_connection, job
):
    """
    Test the process_interaction_loop method to verify it handles job cancellation correctly.

    Mocks:
        - query_llm: Simulates LLM responses.
        - fabric.Connection: Mocks the SSH connection behavior.
        - update_job_status: Verifies that job status updates are called appropriately.

    Args:
        mock_update_job_status (MagicMock): Mock for updating job status.
        mock_query_llm (MagicMock): Mock for querying the LLM.
        mock_fabric_connection (MagicMock): Mock for fabric.Connection.
        job: The job instance being tested.

    Asserts:
        - Confirms the job is marked as canceled.
        - Verifies the job status is updated to "Canceled".
    """
    # Setup mock responses
    mock_query_llm.side_effect = ["command1", "command2"]

    # Mock SSH connection behavior
    mock_ssh_connection = MagicMock()
    mock_ssh_connection.run.return_value.stdout.strip.return_value = "Command executed"
    mock_fabric_connection.return_value.__enter__.return_value = mock_ssh_connection

    # Override is_job_canceled to simulate job cancellation
    job.is_job_canceled = MagicMock(return_value=True)

    # Initialize messages and connect_args
    messages = job.initialize_messages()
    connect_args = job.setup_ssh_connection_params()

    # Run the process_interaction_loop
    job.process_interaction_loop(messages, connect_args)

    assert job.is_job_canceled.called
    mock_update_job_status.assert_any_call(job.job_id, "Canceled")


@patch("ssherlock_runner.fabric.Connection")
@patch("ssherlock_runner.Runner.query_llm")
@patch("ssherlock_runner.update_job_status")
def test_run_function(
    mock_update_job_status, mock_query_llm, mock_fabric_connection, job
):
    """
    Test the run method of the Runner class to ensure it executes the interaction loop properly.

    Mocks:
        - query_llm: Simulates LLM responses.
        - fabric.Connection: Mocks the SSH connection behavior.
        - update_job_status: Verifies that job status updates are called appropriately.

    Args:
        mock_update_job_status (MagicMock): Mock for updating job status.
        mock_query_llm (MagicMock): Mock for querying the LLM.
        mock_fabric_connection (MagicMock): Mock for fabric.Connection.
        job: The job instance being tested.

    Asserts:
        - Checks that the job status transitions from "Running" to "Completed".
        - Verifies the correct number of LLM queries are made.
        - Ensures SSH commands are executed.
    """
    # Setup mocks
    mock_query_llm.side_effect = ["command1", "DONE"]

    # Mock SSH connection behavior
    mock_ssh_connection = MagicMock()
    mock_ssh_connection.run.return_value.stdout = "Server is reachable"
    mock_fabric_connection.return_value.__enter__.return_value = mock_ssh_connection

    # Run the runner's run method
    job.run()

    mock_update_job_status.assert_any_call(job.job_id, "Running")
    mock_update_job_status.assert_any_call(job.job_id, "Completed")
    assert mock_query_llm.call_count == 2
    assert mock_ssh_connection.run.called


def test_update_conversation_normal():
    """
    Test the update_conversation function to ensure it updates conversation messages correctly.

    Verifies normal behavior when both LLM and SSH replies are provided.

    Asserts:
        - Checks that the conversation messages are updated with new entries.
    """
    # Initial conversation messages
    messages = [
        {"role": "system", "content": "You're a helpful AI assistant."},
        {"role": "user", "content": "What is the capital of Japan?"},
        {"role": "assistant", "content": "Tokyo"},
    ]

    # LLM and SSH replies
    llm_reply = "What is its population?"
    ssh_reply = "Approximately 126 million."

    # Call the update_conversation function
    update_conversation(messages, llm_reply, ssh_reply)

    # Expected messages after update
    expected_messages = [
        {"role": "system", "content": "You're a helpful AI assistant."},
        {"role": "user", "content": "What is the capital of Japan?"},
        {"role": "assistant", "content": "Tokyo"},
        {"role": "assistant", "content": "What is its population?"},
        {"role": "user", "content": "Approximately 126 million."},
    ]

    assert messages == expected_messages


def test_update_conversation_empty_replies():
    """
    Test the update_conversation function to ensure it handles empty replies correctly.

    Verifies behavior when both LLM and SSH replies are empty.

    Asserts:
        - Checks that the conversation messages are updated with empty entries.
    """
    # Initial conversation messages
    messages = [
        {"role": "system", "content": "You're a helpful AI assistant."},
        {"role": "user", "content": "What is the capital of Japan?"},
    ]

    # Empty LLM and SSH replies
    llm_reply = ""
    ssh_reply = ""

    # Call the update_conversation function
    update_conversation(messages, llm_reply, ssh_reply)

    # Expected messages after update
    expected_messages = [
        {"role": "system", "content": "You're a helpful AI assistant."},
        {"role": "user", "content": "What is the capital of Japan?"},
        {"role": "assistant", "content": ""},
        {"role": "user", "content": ""},
    ]

    assert messages == expected_messages


def test_update_conversation_large_ssh_reply():
    """
    Test the update_conversation function to ensure it handles large SSH replies correctly.

    Verifies behavior when SSH reply contains substantial information.

    Asserts:
        - Checks that the conversation messages are updated with large SSH reply entries.
    """
    # Initial conversation messages
    messages = [
        {"role": "system", "content": "You're a helpful AI assistant."},
        {"role": "user", "content": "Run a disk check."},
    ]

    # LLM reply and large SSH reply
    llm_reply = "Check disk usage."
    ssh_reply = "Disk usage: 95% full. Please clean up space."

    # Call the update_conversation function
    update_conversation(messages, llm_reply, ssh_reply)

    # Expected messages after update
    expected_messages = [
        {"role": "system", "content": "You're a helpful AI assistant."},
        {"role": "user", "content": "Run a disk check."},
        {"role": "assistant", "content": "Check disk usage."},
        {"role": "user", "content": "Disk usage: 95% full. Please clean up space."},
    ]

    assert messages == expected_messages


@patch("ssherlock_runner.os.getenv")
def test_get_runner_number_success(mock_getenv):
    """Test get_runner_number when RUNNER_NUMBER is set."""
    mock_getenv.return_value = "5"
    assert get_runner_number() == "5"
    mock_getenv.assert_called_once_with("RUNNER_NUMBER")


@patch("ssherlock_runner.os.getenv")
def test_get_runner_number_not_set(mock_getenv):
    """Test get_runner_number when RUNNER_NUMBER is not set."""
    mock_getenv.return_value = None
    with pytest.raises(EnvironmentError, match="RUNNER_NUMBER environment variable is not set."):
        get_runner_number()
    mock_getenv.assert_called_once_with("RUNNER_NUMBER")


@patch("ssherlock_runner.os.getenv")
@patch("ssherlock_runner.log.info")
def test_get_runner_number_logging(mock_log_info, mock_getenv):
    """Test that get_runner_number logs the runner number."""
    mock_getenv.return_value = "3"
    get_runner_number()
    mock_log_info.assert_called_once_with("RUNNER_NUMBER: %s", "3")


@patch("ssherlock_runner.run_job")
@patch("ssherlock_runner.request_job")
@patch("ssherlock_runner.time.sleep", return_value=None)  # To skip actual sleeping
def test_main_successful_job_retrieval(_, mock_request_job, mock_run_job):
    """
    Test the main function to ensure successful job retrieval and processing.

    Mocks:
        - request_job: Simulates job retrieval with initial None response and subsequent valid job.
        - run_job: Verifies that the retrieved job is processed.
        - time.sleep
    : Simulates time delay without actual sleeping.

    Asserts:
        - Checks that the job retrieval is attempted multiple times.
        - Verifies that the job is run once it is successfully retrieved.
    """
    # First call returns None to simulate waiting
    mock_request_job.side_effect = [
        None,
        {
            "id": "job123",
            "llm_api_baseurl": "http://api.example.com",
            "instructions": "Do this",
            "target_host_hostname": "host1",
            "credentials_for_target_hosts_username": "user",
            "llm_api_api_key": "key",
            "credentials_for_target_hosts_password": "pass",
            "bastion_host_hostname": "",
            "credentials_for_bastion_host_username": "",
            "credentials_for_bastion_host_password": "",
        },
        StopIteration,
    ]

    main(max_attempts=3)

    assert mock_request_job.call_count >= 3
    mock_run_job.assert_called_once_with(
        {
            "id": "job123",
            "llm_api_baseurl": "http://api.example.com",
            "instructions": "Do this",
            "target_host_hostname": "host1",
            "credentials_for_target_hosts_username": "user",
            "llm_api_api_key": "key",
            "credentials_for_target_hosts_password": "pass",
            "bastion_host_hostname": "",
            "credentials_for_bastion_host_username": "",
            "credentials_for_bastion_host_password": "",
        }
    )


@patch("ssherlock_runner.run_job")
@patch("ssherlock_runner.request_job")
@patch("ssherlock_runner.time.sleep", return_value=None)
def test_main_no_jobs_available(_, mock_request_job, mock_run_job):
    """
    Test the main function to ensure it handles scenarios where no jobs are initially available.

    Mocks:
        - request_job: Always returns None initially, then a valid job.
        - run_job: Verifies that the job is processed once available.
        - time.sleep: Simulates time delay without actual sleeping.

    Asserts:
        - Ensures the function loops until a job is found.
        - Verifies that the job is run once it is successfully retrieved.
    """
    # Mock request_job to always return None
    mock_request_job.side_effect = [None, None, {"id": "job123"}]

    main(max_attempts=3)

    assert mock_request_job.call_count >= 3  # Ensure it loops until a job is found
    mock_run_job.assert_called_once_with({"id": "job123"})


@patch("ssherlock_runner.run_job")
@patch("ssherlock_runner.request_job")
@patch("ssherlock_runner.time.sleep", return_value=None)
def test_main_exception_handling_in_request_job(_, mock_request_job, mock_run_job):
    """
    Test the main function to ensure it handles exceptions during job requests gracefully.

    Mocks:
        - request_job: Raises an exception on the first call, then returns a valid job.
        - run_job: Verifies that the job is processed once available.
        - time.sleep: Simulates time delay without actual sleeping.

    Asserts:
        - Confirms the function retries after encountering an exception.
        - Verifies that the job is run once it is successfully retrieved.
    """
    # Mock request_job to raise an exception on first call, then return a job
    mock_request_job.side_effect = [Exception("Network error"), {"id": "job123"}]

    main(max_attempts=3)

    assert mock_request_job.call_count >= 3
    mock_run_job.assert_called_once_with({"id": "job123"})
