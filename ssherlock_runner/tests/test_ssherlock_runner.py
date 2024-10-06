"""Test the functions in the runner."""

# pylint: disable=import-error, wrong-import-position
import sys
import threading
import time
import requests
from queue import Empty
import multiprocessing
from unittest.mock import MagicMock
from unittest.mock import patch
from unittest import TestCase
import fabric
import json

import openai
import pytest

sys.path.insert(1, "../")
import ssherlock_runner
from ssherlock_runner import (
    Runner,
    strip_eot_from_string,
    is_string_too_long,
    count_tokens,
    is_llm_done,
    update_job_status,
    run_job,
    request_job,
    log,
)


SSHERLOCK_SERVER_DOMAIN = "localhost:8000"
SSHERLOCK_SERVER_PROTOCOL = "http"
SSHERLOCK_SERVER_RUNNER_TOKEN = "myprivatekey"


@pytest.fixture
def runner():
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


def test_context_size_warning_check(runner):
    """Ensure we get warned properly when the context is about to be exceeded."""
    messages = [
        {"role": "system", "content": "You're a helpful AI assistant."},
        {"role": "user", "content": "What is the capital of Japan?"},
        {"role": "assistant", "content": "Tokyo"},
    ]
    assert runner.context_size_warning_check(messages, threshold=0.85) is True

    # If the model context size isn't set, the function should return false.
    runner = Runner(
        job_id="123",
        llm_api_base_url="test",
        initial_prompt="test",
        target_host_hostname="test",
        credentials_for_target_hosts_username="test",
        model_context_size=0,
    )
    assert runner.context_size_warning_check(messages, threshold=0.85) is False

    runner = Runner(
        job_id="123",
        llm_api_base_url="test",
        initial_prompt="test",
        target_host_hostname="test",
        credentials_for_target_hosts_username="test",
        model_context_size=10000,
    )
    assert runner.context_size_warning_check(messages, threshold=0.85) is False


def test_is_llm_done():
    """Ensure we can detect when the LLM is done."""
    assert is_llm_done("DONE") is True
    assert is_llm_done("Not done") is False
    assert is_llm_done("done") is False


def test_initialize_messages(runner):
    """Ensure the initial prompt gets added properly."""
    messages = runner.initialize_messages()
    assert len(messages) == 2
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Initial prompt example message."


def test_setup_ssh_connection_params_with_keyfile():
    """Ensure the SSH connect args use a keyfile when one is passed."""
    runner = Runner(
        job_id="123",
        llm_api_base_url="test",
        initial_prompt="test",
        target_host_hostname="test",
        credentials_for_target_hosts_username="test",
        credentials_for_target_hosts_keyfile="/path/to/keyfile",
    )
    connect_args = runner.setup_ssh_connection_params()
    assert connect_args["key_filename"] == "/path/to/keyfile"


def test_setup_ssh_connection_params_with_password():
    """Ensure the SSH connect args use a password when one is passed."""
    runner = Runner(
        job_id="123",
        llm_api_base_url="test",
        initial_prompt="test",
        target_host_hostname="test",
        credentials_for_target_hosts_username="test",
        credentials_for_target_hosts_password="pass123",
    )
    connect_args = runner.setup_ssh_connection_params()
    print(connect_args)
    assert connect_args["password"] == "pass123"


def test_query_llm(runner):
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
        response = runner.query_llm(prompt)
        assert response == "Tokyo"


def test_can_llm_be_reached_success(runner):
    """Ensure the correct bool is returned when we check the reachability of the LLM and succeed."""
    with patch.object(runner, "query_llm", return_value="GOOD"):
        assert runner.can_llm_be_reached() is True


def test_can_llm_be_reached_failure(runner):
    """Ensure the correct bool is returned when we check the reachability of the LLM and fail."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.reason = "Internal Server Error"
    with patch.object(
        runner,
        "query_llm",
        side_effect=openai.InternalServerError(
            response=mock_response, body="Error", message="Error"
        ),
    ):
        assert runner.can_llm_be_reached() is False


def test_wait_for_llm_to_become_available_success(runner):
    """Ensure waiting for LLM to be available after multiple failed attempts works correctly."""

    with patch.object(runner, "can_llm_be_reached", side_effect=[False, False, True]):
        # Mock sleep to speed up the test.
        with patch("time.sleep", return_value=None):
            runner.wait_for_llm_to_become_available()


def test_wait_for_llm_to_become_available_timeout(runner):
    """Ensure waiting for the LLM to become available and timing out throws an error."""

    with patch.object(runner, "can_llm_be_reached", return_value=False):
        # Mock sleep to speed up the test.
        with patch("time.sleep", return_value=None):
            with pytest.raises(
                RuntimeError,
                match="Timed out waiting for LLM server to become available!",
            ):
                runner.wait_for_llm_to_become_available()


def test_summarize_string(runner):
    """Mock the OpernAI API to test string summarization function."""
    string_to_summarize = "This is a long text that needs to be summarized."

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Summarized text"
    mock_client.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client):
        summary = runner.summarize_string(string_to_summarize)
        assert summary == "Summarized text"


def test_run_ssh_cmd_with_sudo(runner):
    """Ensure stdout and stderr get combined correctly in mocked SSH command with sudo."""
    runner.credentials_for_target_hosts_sudo_password = "sudo_password"

    mock_connection = MagicMock()
    mock_result = MagicMock()
    mock_result.stdout.strip.return_value = "Command output"
    mock_result.stderr.strip.return_value = "Error output"
    mock_connection.sudo.return_value = mock_result

    command_output = runner.run_ssh_cmd(mock_connection, "echo Hello")
    assert command_output == "Command outputError output"


def test_run_ssh_cmd_without_sudo(runner):
    """Ensure stdout and stderr get combined correctly in mocked SSH command without sudo."""
    runner.target_host_user_sudo_password = ""

    mock_connection = MagicMock()
    mock_result = MagicMock()
    mock_result.stdout.strip.return_value = "Command output"
    mock_result.stderr.strip.return_value = "Error output"
    mock_connection.run.return_value = mock_result

    command_output = runner.run_ssh_cmd(mock_connection, "echo Hello")
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
#         runner.run_ssh_cmd(mock_connection, "ls -la")

#     assert str(context.exception) == "Command execution failed"
#     mock_log_error.assert_called_once_with("SSH command failed: %s", "Command execution failed")
#     mock_update_status.assert_called_once_with("1234567890abcdef", "Failed")


def test_handle_ssh_command_no_summarization(runner):
    """Ensure running an SSH command works correctly without output summarization."""
    mock_ssh = MagicMock()
    mock_llm_reply = "ls -1"
    mock_ssh_reply = "dir1 dir2 dir3 file1.txt file2.txt"

    with patch.object(runner, "run_ssh_cmd", return_value=mock_ssh_reply):
        response = runner.handle_ssh_command(mock_ssh, mock_llm_reply)
        assert response == mock_ssh_reply


def test_handle_ssh_command_with_summarization(runner):
    """Ensure running an SSH command works correctly with output summarization."""
    mock_ssh = MagicMock()
    mock_llm_reply = "ls -1"
    mock_ssh_reply = "dir1 dir2 dir3 file1.txt file2.txt"
    summarized_output = "A list of directories and files."

    # Patch both the run_ssh_cmd method and the is_string_too_long method.
    with patch.object(runner, "run_ssh_cmd", return_value=mock_ssh_reply), patch(
        "ssherlock_runner.is_string_too_long", return_value=True
    ), patch.object(runner, "summarize_string", return_value=summarized_output):

        # When the string is too long, it should be summarized.
        response = runner.handle_ssh_command(mock_ssh, mock_llm_reply)
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
    with patch(
        "requests.post", side_effect=Exception("Connection error")
    ) as mock_post, patch("ssherlock_runner.log.error") as mock_log_error:

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

    with patch("ssherlock_runner.update_job_status") as mock_update_status, patch(
        "ssherlock_runner.Runner"
    ) as MockRunner:

        mock_runner_instance = MockRunner.return_value
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
    ) as mock_get, patch("ssherlock_runner.log.error") as mock_log_error:

        result = request_job()
        assert result is None

        # Verify that an error was logged with the correct format.
        mock_log_error.assert_called_once()
        args, kwargs = mock_log_error.call_args
        assert args[0] == "Error fetching job: %s"
        assert str(args[1]) == "Network error"


@patch("ssherlock_runner.Runner.wait_for_llm_to_become_available")
@patch("ssherlock_runner.Runner.can_target_server_be_reached", return_value=True)
def test_initialize_success(mock_can_reach, mock_wait_llm, runner):
    """Test initialize method when the target server can be reached."""
    runner.initialize()
    mock_can_reach.assert_called_once()
    mock_wait_llm.assert_called_once()


@patch("ssherlock_runner.log.critical")
@patch("ssherlock_runner.Runner.wait_for_llm_to_become_available")
@patch("ssherlock_runner.Runner.can_target_server_be_reached", return_value=False)
def test_initialize_failure(mock_log_critical, mock_wait_llm, mock_can_reach, runner):
    """Test initialize method when the target server cannot be reached."""
    with TestCase.assertRaises(TestCase(), RuntimeError):
        runner.initialize()

    mock_can_reach.assert_called_once()
    mock_log_critical.assert_called_once()
    mock_wait_llm.assert_not_called()


@patch("ssherlock_runner.log.warning")
@patch("ssherlock_runner.log.error")
@patch("ssherlock_runner.update_job_status")
@patch("ssherlock_runner.fabric.Connection")
def test_can_target_server_be_reached_success(
    mock_connection, mock_update_status, mock_log_error, mock_log_warning, runner
):
    """Test can_target_server_be_reached method when the server is reachable."""
    runner.setup_ssh_connection_params = MagicMock(return_value={"key": "value"})

    # Mock the run method of fabric.Connection to simulate successful command execution
    mock_connection.return_value.__enter__.return_value.run = MagicMock()

    result = runner.can_target_server_be_reached()

    assert result == True
    mock_log_warning.assert_called_once_with("Checking target server reachability...")
    mock_log_error.assert_not_called()
    mock_update_status.assert_not_called()


@patch("ssherlock_runner.log.warning")
@patch("ssherlock_runner.log.error")
@patch("ssherlock_runner.update_job_status")
@patch("ssherlock_runner.fabric.Connection")
def test_can_target_server_be_reached_failure(
    mock_connection, mock_update_status, mock_log_error, mock_log_warning, runner
):
    """Test can_target_server_be_reached method when the server is not reachable."""
    runner.setup_ssh_connection_params = MagicMock(return_value={"key": "value"})

    # Simulate an exception being raised during the SSH connection attempt
    mock_connection.side_effect = Exception("Connection failed")

    result = runner.can_target_server_be_reached()

    assert result == False
    mock_log_warning.assert_called_once_with("Checking target server reachability...")
    mock_log_error.assert_called_once_with(
        "Failed to reach the target server: %s", str(Exception("Connection failed"))
    )
    mock_update_status.assert_called_once_with("1234567890abcdef", "Failed")


@patch("ssherlock_runner.requests.get")
@patch("ssherlock_runner.log.error")
def test_is_job_canceled_success(mock_log_error, mock_requests_get, runner):
    """Test is_job_canceled method when job status is 'Canceled'."""

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"status": "Canceled"}
    mock_requests_get.return_value = mock_response

    result = runner.is_job_canceled()

    assert result is True
    mock_log_error.assert_not_called()


@patch("ssherlock_runner.requests.get")
@patch("ssherlock_runner.log.error")
def test_is_job_canceled_not_canceled(mock_log_error, mock_requests_get, runner):
    """Test is_job_canceled method when job status is not 'Canceled'."""

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"status": "Running"}
    mock_requests_get.return_value = mock_response

    result = runner.is_job_canceled()

    assert result is False
    mock_log_error.assert_not_called()


@patch("ssherlock_runner.requests.get")
@patch("ssherlock_runner.log.error")
def test_is_job_canceled_failure(mock_log_error, mock_requests_get, runner):
    """Test is_job_canceled method when an exception occurs."""

    # Simulate a RequestException being raised
    mock_requests_get.side_effect = requests.RequestException("Network error")

    result = runner.is_job_canceled()

    assert result is False
    mock_log_error.assert_called_once_with(
        "Error checking job status: %s", "Network error"
    )
