import logging as log
import time

import fabric
import openai
import tiktoken


LOG_LEVEL = "WARNING"

INITIAL_PROMPT = "Install nginx and configure it to use a self-signed TLS certificate."

SYSTEM_PROMPT = (
    "You're an autonomous system administrator managing a server non-interactively."
    "Your objective is to print the next command to run to complete the task and NOTHING ELSE!"
    "You must follow these rules:"
    "1. If your objective has been completed successfully, print DONE."
    "2. Prepend privileged actions with sudo."
    "3. Don't use tools that require interaction with the terminal, like vim or nano."
    "4. Don't include explanations of anything, only print commands."
    "5. Don't print multiple commands at one time."
    "6. If you get a 'Permission denied' error, try a different method."
    "7. Add -y to package installation commands."
)

# This is used to provide the user a warning if context size is about to be exceeded.
MODEL_CONTEXT_SIZE = 128000


def configure_logging(log_level: str) -> None:
    """Set up logging."""
    log.basicConfig(
        format="%(asctime)s %(funcName)s: %(message)s", level=log_level.upper()
    )
    log.debug("Logging has been configured at a level of: %s", log_level.upper())


def strip_eot_from_string(string: str) -> str:
    """
    Strip the <|eot_id|> from the end of the LLM response for more human-readable output.

    Args:
        string (string): The string you wish to strip the EOT from.

    Returns:
        Returns the input string with <|eot_id|> stripped.
    """
    log.debug("Running strip_eot_from_string(%s)", string)
    return string[:-10]


def query_llm(base_url: str, prompt) -> str:
    """
    Send a prompt to an LLM API and return its reply. LLM API must be OpenAI-compatible.

    Args:
        base_url (string): The base URL of the LLM API, like "https://codeium.gmcsde.com/v1".
        prompt (list of dicts): The LLM prompt, including system prompt. Previous responses from the
                                LLM can also be added as context for new replies in order to mimic
                                a conversation. See example below.

    Example:
        prompt = [
            {"role": "system", "content": "You're a helpful AI assistant.",},
            {"role": "user", "content": "What is the capital of Japan?",},
            {"role": "assistant", "content": "Tokyo",},
            {"role": "user", "content": "What is its population?",},
        ]

    Returns:
        Returns the LLM's reponse as a string.
    """
    log.debug("Running query_llm(%s)", prompt)

    client = openai.OpenAI(
        base_url=base_url,
        api_key="sk-no-key-required",
    )

    llm_reply = client.chat.completions.create(
        model="llama3.1",
        messages=prompt,
    )

    response_string = llm_reply.choices[0].message.content
    response_string_stripped = strip_eot_from_string(response_string)
    return response_string_stripped


def can_llm_be_reached() -> bool:
    """
    Check if the LLM API can be reached with a quick prompt.

    Returns:
        Returns True if the API can be reached, returns False otherwise.
    """
    prompt = [
        {
            "role": "system",
            "content": "You're a helpful AI assistant.",
        },
        {
            "role": "user",
            "content": "Print GOOD and nothing else.",
        },
    ]
    try:
        query_llm("https://codeium.gmcsde.com/v1", prompt)
        return True
    except openai.InternalServerError:
        return False


def wait_for_llm_to_become_available() -> None:
    """
    Wait in a loop until the LLM API can be reached successfully.

    Raises:
        Raises a RuntimeError if waiting times out.
    """
    log.warning("Checking LLM connectivity...")
    for i in range(100):
        if can_llm_be_reached() is False:
            log.warning("Waiting for LLM server to become available ... %s/100", i)
            time.sleep(10)
        else:
            return
    raise RuntimeError("Timed out waiting for LLM server to become available!")


def is_string_too_long(string: str, threshold: int = 1000) -> bool:
    """
    Determine if the given string is longer than a certain threshold.

    This is used to help us figure out if the LLM output needs to be summarized to reduce context size.

    Args:
        string (string): The input string to check.
        threshold (int): The input string will be checked if it's longer than the threshold length.
                         Default is 1000.

    Returns:
        Returns True if string is longer than the threshold, otherwise returns false.
    """
    log.debug("Running is_string_too_long(%s)", string)
    if len(string) > threshold:
        return True
    return False


def summarize_string(string: str) -> str:
    """
    Summarize the given string with the LLM API.

    This is done so longer strings can better fit into the LLM's context window during long
    conversations.

    Args:
        string (string): The given string to summarize with the LLM.

    Returns:
        Returns the summarized string as a string.
    """
    log.debug("Running summarize_string(%s)", string)
    system_prompt = (
        "You are a helpful AI assistant that summarizes text."
        "Your objective is to summarize all text that is provided to you as input and NOTHING ELSE!"
        "You must follow these rules:"
        "1. Be brief"
        "2. All summaries must be a single line."
        "3. Only include the most important and relevant information."
        "3. Don't be verbose."
        "4. Don't summarize over multiple lines."
    )
    prompt = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": string,
        },
    ]
    llm_summarization = query_llm("https://codeium.gmcsde.com/v1", prompt)
    log.warning("SSH reply was summarized to: %s", llm_summarization)
    return llm_summarization


def count_tokens(messages) -> int:
    """
    Count the number of LLM tokens in the provided dictionary of context.

    Uses the list of dictionaries inside the messages list and counts the tokens in the "content" key.

    Args:
        messages (list of dicts): Counts tokens in the "content" key of each dictionary in the
                                  provided list. See examples below.

    Examples:
        messages = [
            {"role": "system", "content": "You're a helpful AI assistant.",},
            {"role": "user", "content": "What is the capital of Japan?",},
            {"role": "assistant", "content": "Tokyo",},
        ]

    Returns:
        Returns the number of tokens as an int.
    """
    log.debug("Running count_tokens(%s)", messages)
    content_string = " ".join(message["content"] for message in messages)

    encoding = tiktoken.encoding_for_model("gpt-4o")
    tokens = encoding.encode(content_string)

    num_tokens = len(tokens)
    return num_tokens


def context_size_warning_check(messages, threshold=0.85) -> None:
    """
    Print a warning if we're about to exceed the context size of the model.

    Args:
        messages (list of dicts): Counts tokens in the "content" key of each dictionary in the
                                  provided list to determine if we're near the context size threshold
                                  of the LLM. See examples below.

        threshold (float): A decimal between 0 and 1 to determine the threshold of the LLM's context
                           size to warn after. For example, a threshold of "0.85" will warn after
                           we've exceeded 85% of the LLM's context size. Default is 0.85.

    Examples:
        messages = [
            {"role": "system", "content": "You're a helpful AI assistant.",},
            {"role": "user", "content": "What is the capital of Japan?",},
            {"role": "assistant", "content": "Tokyo",},
        ]

    """
    log.debug("Running context_size_warning_check(%s)", messages)
    num_tokens = count_tokens(messages)
    log.warning("Currently using %s tokens", num_tokens)
    if num_tokens > (threshold * MODEL_CONTEXT_SIZE):
        log.warning("REACHED %s OF MODEL CONTEXT SIZE", str(threshold))
    return


def is_llm_done(llm_reply: str) -> bool:
    """
    Check if the LLM has finished with its objective.

    Args:
        llm_reply (str): The reply from the LLM to analyze to determine if it's finished with its
                         objective.

    Returns:
        Returns True if the LLM is finished, returns false otherwise.
    """
    log.debug("Running is_llm_done(%s)", llm_reply)
    if llm_reply == "DONE":
        return True
    return False


def run_ssh_cmd(host, user, command, password="", ssh_private_key_file="") -> str:
    """
    Run a command over SSH on the given host and return its output.

    Args:
        host (str): The FQDN or IP of the host to connect to over SSH.
        user (str): The user to connect to the host as.
        command (str): The command to run on the host.
        password (str): The password to authenticate to the host. Optional.
        ssh_private_key_file (str): The path to the SSH key used to authenticate to the host. If
                                    this arg is used, the "password" arg is ignored.

    Returns:
        Returns the SSH command output. Both stdout and stderr are combined into a single string.
    """
    log.debug(
        "Running run_ssh_cmd(%s, %s, %s, %s, %s)",
        host,
        user,
        password,
        ssh_private_key_file,
        command,
    )
    shell_environment = "DEBIAN_FRONTEND=noninteractive"
    command = shell_environment + " && " + command

    if ssh_private_key_file != "":
        connect_args = {"key_filename": ssh_private_key_file}
    else:
        connect_args = {"password": password}

    with fabric.Connection(host=host, user=user, connect_kwargs=connect_args) as ssh:
        result = ssh.run(command, hide=True, warn=True)

    output = {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    # Combine output streams for the LLM.
    output = output["stdout"] + output["stderr"]
    output_str = str(output)
    log.debug("run_ssh_cmd output is: %s", output_str)
    return output_str


def main():
    configure_logging(LOG_LEVEL)
    log.debug("Running main()")

    wait_for_llm_to_become_available()

    # Set the system prompt and the initial prompt.
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": INITIAL_PROMPT})

    for _ in range(100):

        # Obtain the llm_reply.
        llm_reply = query_llm("https://codeium.gmcsde.com/v1", messages)
        log.warning("LLM reply was: %s", llm_reply)

        # Check if we need to keep going.
        if is_llm_done(llm_reply):
            log.critical("All done!")
            return

        # If the LLM isn't done, send the response to the server over SSH
        ssh_reply = run_ssh_cmd(
            host="52.222.114.40",
            user="ubuntu",
            ssh_private_key_file="/home/akelley/keys/aws-devops",
            command=llm_reply,
        )
        log.warning("SSH reply was: %s", ssh_reply)

        if is_string_too_long(ssh_reply):
            ssh_reply = summarize_string(ssh_reply)

        # Update new prompts with the LLM's reply and the server's stdout.
        messages.append({"role": "assistant", "content": llm_reply})
        messages.append({"role": "user", "content": ssh_reply})

        context_size_warning_check(messages)

    log.critical("Ran out of iterations!")


if __name__ == "__main__":
    main()
