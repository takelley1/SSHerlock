"""Test the functions in the runner."""
# pylint: disable=import-error, wrong-import-position
import sys
from unittest.mock import MagicMock
from unittest.mock import patch

import openai
import pytest

sys.path.insert(1, "../")
from ssherlock_runner import (
    Runner,
    strip_eot_from_string,
    is_string_too_long,
    count_tokens,
    is_llm_done,
)


def test_configure_logging():
    """Ensure the correct log level is used."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
        log_level="CRITICAL",
    )
    runner.configure_logging()
    assert runner.log_level == "CRITICAL"


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


def test_context_size_warning_check():
    """Ensure we get warned properly when the context is about to be exceeded."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
        model_context_size=16,
    )
    messages = [
        {"role": "system", "content": "You're a helpful AI assistant."},
        {"role": "user", "content": "What is the capital of Japan?"},
        {"role": "assistant", "content": "Tokyo"},
    ]
    assert runner.context_size_warning_check(messages, threshold=0.85) is True

    # If the model context size isn't set, the function should return false.
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
        model_context_size=0,
    )
    assert runner.context_size_warning_check(messages, threshold=0.85) is False

    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
        model_context_size=10000,
    )
    assert runner.context_size_warning_check(messages, threshold=0.85) is False


def test_is_llm_done():
    """Ensure we can detect when the LLM is done."""
    assert is_llm_done("DONE") is True
    assert is_llm_done("Not done") is False
    assert is_llm_done("done") is False


def test_initialize_messages():
    """Ensure the initial prompt gets added properly."""
    initial_prompt = "Initial prompt here."
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt=initial_prompt,
        target_host="test",
        target_host_user="test",
    )

    messages = runner.initialize_messages()
    assert len(messages) == 2
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == initial_prompt


def test_setup_ssh_connection_params_with_keyfile():
    """Ensure the SSH connect args use a keyfile when one is passed."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
        target_host_user_keyfile="/path/to/keyfile",
    )
    connect_args = runner.setup_ssh_connection_params()
    assert connect_args["key_filename"] == "/path/to/keyfile"


def test_setup_ssh_connection_params_with_password():
    """Ensure the SSH connect args use a password when one is passed."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
        target_host_user_password="pass123",
    )
    connect_args = runner.setup_ssh_connection_params()
    print(connect_args)
    assert connect_args["password"] == "pass123"


def test_query_llm():
    """Ensure querying the LLM returns expected results."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
    )
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


def test_can_llm_be_reached_success():
    """Ensure the correct bool is returned when we check the reachability of the LLM and succeed."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
    )
    with patch.object(runner, "query_llm", return_value="GOOD"):
        assert runner.can_llm_be_reached() is True


def test_can_llm_be_reached_failure():
    """Ensure the correct bool is returned when we check the reachability of the LLM and fail."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
    )
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


def test_wait_for_llm_to_become_available_success():
    """Ensure waiting for LLM to be available after multiple failed attempts works correctly."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
    )

    with patch.object(runner, "can_llm_be_reached", side_effect=[False, False, True]):
        # Mock sleep to speed up the test.
        with patch("time.sleep", return_value=None):
            runner.wait_for_llm_to_become_available()


def test_wait_for_llm_to_become_available_timeout():
    """Ensure waiting for the LLM to become available and timing out throws an error."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
    )

    with patch.object(runner, "can_llm_be_reached", return_value=False):
        # Mock sleep to speed up the test.
        with patch("time.sleep", return_value=None):
            with pytest.raises(
                RuntimeError,
                match="Timed out waiting for LLM server to become available!",
            ):
                runner.wait_for_llm_to_become_available()


def test_summarize_string():
    """Mock the OpernAI API to test string summarization function."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
    )
    string_to_summarize = "This is a long text that needs to be summarized."

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Summarized text"
    mock_client.chat.completions.create.return_value = mock_response

    with patch("openai.OpenAI", return_value=mock_client):
        summary = runner.summarize_string(string_to_summarize)
        assert summary == "Summarized text"


def test_run_ssh_cmd_with_sudo():
    """Ensure stdout and stderr get combined correctly in mocked SSH command with sudo."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
    )
    runner.target_host_user_sudo_password = "sudo_password"

    mock_connection = MagicMock()
    mock_result = MagicMock()
    mock_result.stdout.strip.return_value = "Command output"
    mock_result.stderr.strip.return_value = "Error output"
    mock_connection.sudo.return_value = mock_result

    command_output = runner.run_ssh_cmd(mock_connection, "echo Hello")
    assert command_output == "Command outputError output"


def test_run_ssh_cmd_without_sudo():
    """Ensure stdout and stderr get combined correctly in mocked SSH command without sudo."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
    )
    runner.target_host_user_sudo_password = ""

    mock_connection = MagicMock()
    mock_result = MagicMock()
    mock_result.stdout.strip.return_value = "Command output"
    mock_result.stderr.strip.return_value = "Error output"
    mock_connection.run.return_value = mock_result

    command_output = runner.run_ssh_cmd(mock_connection, "echo Hello")
    assert command_output == "Command outputError output"


def test_handle_ssh_command_no_summarization():
    """Ensure running an SSH command works correctly without output summarization."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
    )

    mock_ssh = MagicMock()
    mock_llm_reply = "ls -1"
    mock_ssh_reply = "dir1 dir2 dir3 file1.txt file2.txt"

    with patch.object(runner, "run_ssh_cmd", return_value=mock_ssh_reply):
        response = runner.handle_ssh_command(mock_ssh, mock_llm_reply)
        assert response == mock_ssh_reply


def test_handle_ssh_command_with_summarization():
    """Ensure running an SSH command works correctly with output summarization."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
    )

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


def test_main():
    """Test code for the main function."""
    runner = Runner(
        llm_api_base_url="test",
        initial_prompt="test",
        target_host="test",
        target_host_user="test",
    )

    with patch.object(runner, "initialize") as mock_initialize, patch.object(
        runner, "initialize_messages"
    ) as mock_initialize_messages, patch.object(
        runner, "setup_ssh_connection_params"
    ) as mock_setup_ssh_connection_params, patch.object(
        runner, "process_interaction_loop"
    ) as mock_process_interaction_loop:

        runner.main()

        mock_initialize.assert_called_once()
        mock_initialize_messages.assert_called_once()
        mock_setup_ssh_connection_params.assert_called_once()
        mock_process_interaction_loop.assert_called_once_with(
            mock_initialize_messages.return_value,
            mock_setup_ssh_connection_params.return_value,
        )
