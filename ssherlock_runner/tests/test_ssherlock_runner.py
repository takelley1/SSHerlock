# pylint: disable=import-error
import os
import sys

import pytest

sys.path.insert(1, "../")
from ssheldon import (
    Runner,
    strip_eot_from_string,
    is_string_too_long,
    count_tokens,
    is_llm_done,
)


# Set required environment variables
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["INITIAL_PROMPT"] = "test"
os.environ["TARGET_HOST"] = "test.com"
os.environ["TARGET_HOST_USER"] = "test"
os.environ["LLM_API_BASE_URL"] = "test.example.com"


def test_strip_eot_from_string():
    assert strip_eot_from_string("Hello, World!<|eot_id|>") == "Hello, World!"
    assert strip_eot_from_string("Hello, World!") == "Hello, World!"


def test_is_string_too_long():
    assert is_string_too_long("a" * 1001) is True
    assert is_string_too_long("a" * 1000) is False
    assert is_string_too_long("a" * 999) is False
    assert is_string_too_long("a" * 501, threshold=500) is True
    assert is_string_too_long("a" * 499, threshold=500) is False


def test_count_tokens():
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "What is the capital of Japan?"},
        {"role": "assistant", "content": "Tokyo"},
    ]
    assert count_tokens(messages) == 15


def test_context_size_warning_check():
    os.environ["MODEL_CONTEXT_SIZE"] = "16"
    runner = Runner()
    print(runner.model_context_size)

    messages = [
        {"role": "system", "content": "You're a helpful AI assistant."},
        {"role": "user", "content": "What is the capital of Japan?"},
        {"role": "assistant", "content": "Tokyo"},
    ]
    assert runner.context_size_warning_check(messages, threshold=0.85) is True

    #  with patch("your_module_name.count_tokens", return_value=80):
    #      caplog.clear()
    #      context_size_warning_check(messages, threshold=0.85)
    #      assert "REACHED 0.85 OF MODEL CONTEXT SIZE" not in caplog.text


def test_is_llm_done():
    assert is_llm_done("DONE") is True
    assert is_llm_done("Not done") is False
    assert is_llm_done("done") is False


def test_initialize_messages():
    system_prompt = "System prompt here."
    initial_prompt = "Initial prompt here."

    messages = initialize_messages(system_prompt, initial_prompt)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == system_prompt
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == initial_prompt


def test_setup_ssh_connection_params_with_keyfile(config):
    config.target_host_user_keyfile = "/path/to/keyfile"
    connect_args = setup_ssh_connection_params()
    assert connect_args["key_filename"] == "/path/to/keyfile"


def test_setup_ssh_connection_params_with_password(config):
    config.target_host_user_keyfile = ""
    config.target_host_user_password = "supersecurepassword"
    connect_args = setup_ssh_connection_params()
    assert connect_args["password"] == "supersecurepassword"
