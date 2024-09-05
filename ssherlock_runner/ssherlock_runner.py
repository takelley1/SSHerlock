"""Main runner."""

# pylint: disable=import-error
import logging as log
import time

import fabric
import openai
import tiktoken


def log_function_call(func):
    """Easily decorage functions with @log_function_call to log calls."""

    def wrapper(*args, **kwargs):
        log.debug("Calling %s with args=%s, kwargs=%s", func.__name__, args, kwargs)
        result = func(*args, **kwargs)
        log.debug("%s returned %s", func.__name__, result)
        return result

    return wrapper


class Runner:  # pylint: disable=too-many-arguments
    """Main class for runner configuration."""

    def __init__(
        self,
        llm_api_base_url,
        initial_prompt,
        target_host,
        target_host_user,
        llm_api_key="",
        model_context_size=0,
        log_level="WARNING",
        target_host_user_password="",
        target_host_user_keyfile="",
        target_host_user_sudo_password="",
        bastion_host="",
        bastion_host_user="",
        bastion_host_user_password="",
        bastion_host_user_keyfile="",
    ):
        """Initialize main runner configuration."""
        self.log_level = log_level
        self.initial_prompt = initial_prompt
        self.model_context_size = model_context_size
        self.target_host = target_host
        self.target_host_user = target_host_user
        self.target_host_user_password = target_host_user_password
        self.target_host_user_keyfile = target_host_user_keyfile
        self.target_host_user_sudo_password = target_host_user_sudo_password
        self.bastion_host = bastion_host
        self.bastion_host_user = bastion_host_user
        self.bastion_host_user_password = bastion_host_user_password
        self.bastion_host_user_keyfile = bastion_host_user_keyfile
        self.llm_api_base_url = llm_api_base_url
        self.llm_api_key = llm_api_key
        self.shell_environment = "DEBIAN_FRONTEND=noninteractive ASSUME_YES=1 LC_ALL=C"
        self.system_prompt = (
            "You're an autonomous system administrator managing a server non-interactively."
            "Your objective is print the next command to run to complete the task and NOTHING ELSE!"
            "You MUST FOLLOW ALL THE FOLLOWING RULES EXACTLY:"
            "1. If your objective has been completed successfully, print DONE."
            "2. Prepend privileged actions with sudo."
            "3. Don't use tools that require interaction with the terminal, like vim or nano."
            "4. Don't include explanations of anything, only print commands."
            "5. Don't print multiple commands at one time."
            "6. If you get a 'Permission denied' error, try a different method."
            "7. Add -y to package installation commands."
            "8. If you get errors of any kind, try a different command."
        )
        self.system_prompt_summarize = (
            "You are a helpful AI assistant that summarizes text."
            "Your objective is to summarize all text that is provided to you as input and \
            NOTHING ELSE!"
            "You must follow these rules:"
            "1. Be brief"
            "2. All summaries must be a single line."
            "3. Only include the most important and relevant information."
            "3. Don't be verbose."
            "4. Don't summarize over multiple lines."
        )

    def configure_logging(self) -> None:
        """Set up logging."""
        log.basicConfig(
            format="%(asctime)s %(funcName)s: %(message)s", level=self.log_level.upper()
        )
        log.debug(
            "Logging has been configured at a level of: %s", self.log_level.upper()
        )

    @log_function_call
    def initialize(self) -> None:
        """Run general setup and safety checks."""
        self.configure_logging()
        self.wait_for_llm_to_become_available()

    @log_function_call
    def query_llm(self, prompt) -> str:
        """
        Send a prompt to an LLM API and return its reply. LLM API must be OpenAI-compatible.

        Args:
            base_url (string): The base URL of the LLM API, like "https://codeium.example.com/v1".
            prompt (list of dicts): The LLM prompt, including system prompt. Previous responses
                                    from the LLM can also be added as context for new replies in
                                    order to mimic a conversation. See example below.

        Example:
            prompt = [
                {"role": "system", "content": "You're a helpful AI assistant.",},
                {"role": "user", "content": "What is the capital of Japan?",},
                {"role": "assistant", "content": "Tokyo",},
                {"role": "user", "content": "What is its population?",},
            ]

        Returns:
            str: LLM's response.
        """
        client = openai.OpenAI(
            base_url=self.llm_api_base_url,
            api_key=self.llm_api_key,
        )

        llm_reply = client.chat.completions.create(
            model="llama3.1",
            messages=prompt,
        )

        response_string = llm_reply.choices[0].message.content
        response_string_stripped = strip_eot_from_string(response_string)
        return response_string_stripped

    @log_function_call
    def can_llm_be_reached(self) -> bool:
        """
        Check if the LLM API can be reached with a quick prompt.

        Returns:
            bool: True if the API can be reached, False otherwise.
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
            self.query_llm(prompt=prompt)
            return True
        except openai.InternalServerError:
            return False

    @log_function_call
    def wait_for_llm_to_become_available(self) -> None:
        """
        Wait in a loop until the LLM API can be reached successfully.

        Raises:
            Raises a RuntimeError if waiting times out.
        """
        log.warning("Checking LLM connectivity...")
        for i in range(100):
            if self.can_llm_be_reached() is False:
                log.warning("Waiting for LLM server to become available ... %s/100", i)
                time.sleep(10)
            else:
                return
        raise RuntimeError("Timed out waiting for LLM server to become available!")

    @log_function_call
    def summarize_string(self, string: str) -> str:
        """
        Summarize the given string with the LLM API.

        This is done so longer strings can better fit into the LLM's context window during long
        conversations.

        Args:
            string (string): The given string to summarize with the LLM.

        Returns:
            str: The summarized string.
        """
        prompt = [
            {
                "role": "system",
                "content": self.system_prompt_summarize,
            },
            {
                "role": "user",
                "content": string,
            },
        ]
        llm_summarization = self.query_llm(prompt=prompt)
        log.warning("SSH reply was summarized to: %s", llm_summarization)
        return llm_summarization

    @log_function_call
    def context_size_warning_check(self, messages, threshold=0.85) -> bool:
        """
        Print a warning if we're about to exceed the context size of the model.

        Args:
            messages (list of dicts): Counts tokens in the "content" key of each dictionary in the
                                      provided list to determine if we're near the context size
                                      threshold of the LLM. See examples below.

            threshold (float): A decimal between 0 and 1 to determine the threshold of the LLM's
                               context size to warn after. For example, a threshold of "0.85"
                               will warn after we've exceeded 85% of the LLM's context size.
                               Default is 0.85.

        Examples:
            messages = [
                {"role": "system", "content": "You're a helpful AI assistant.",},
                {"role": "user", "content": "What is the capital of Japan?",},
                {"role": "assistant", "content": "Tokyo",},
            ]

        Returns:
            bool: True if context threshold has been exceeded, False otherwise.
        """
        # Skip if the context size hasn't been set.
        if self.model_context_size == 0:
            print("Returning false since size is 0")
            return False
        num_tokens = count_tokens(messages)
        print("Current token count is ", num_tokens)
        log.warning("Currently using %s tokens", num_tokens)
        if num_tokens > (threshold * self.model_context_size):
            log.warning("REACHED %s OF MODEL CONTEXT SIZE", str(threshold))
            return True
        return False

    @log_function_call
    def run_ssh_cmd(self, connection: fabric.Connection, command: str) -> str:
        """
        Run a command over an existing SSH connection and return its output.

        Args:
            ssh (fabric.Connection): The open SSH connection to use for command execution.
            command (str): The command to run on the host.
            sudo_password (str): The password to use to elevate with sudo.

        Returns:
            str: SSH command output. Both stdout and stderr are combined into a single string.
        """
        command = f"{self.shell_environment} ; {command}"

        if self.target_host_user_sudo_password:
            result = connection.sudo(
                command,
                warn=True,
                pty=True,
                password=self.target_host_user_sudo_password,
            )
        else:
            result = connection.run(command, warn=True, pty=True)

        # Combine output streams for the LLM.
        output = result.stdout.strip() + result.stderr.strip()
        log.debug("run_ssh_cmd output is: %s", output)
        return output

    @log_function_call
    def initialize_messages(self) -> list:
        """
        Initialize the messages list with the system and user prompts.

        Args:
            system_prompt (str): The system's prompt.
            initial_prompt (str): The initial user's prompt.

        Returns:
            list: Initialized messages list.
        """
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.initial_prompt},
        ]

    @log_function_call
    def setup_ssh_connection_params(self) -> dict:
        """
        Prepare SSH connection parameters based on the configuration.

        Args:
            config (Config): Configuration object containing SSH credentials.

        Returns:
            dict: SSH connection parameters.
        """
        if self.target_host_user_keyfile:
            return {"key_filename": self.target_host_user_keyfile}
        return {"password": self.target_host_user_password}

    @log_function_call
    def process_interaction_loop(self, messages: list, connect_args: dict) -> None:
        """
        Process the interaction loop with the LLM and SSH server.

        Args:
            messages (list): The list of messages in the conversation.
            connect_args (dict): SSH connection parameters.
        """
        # Setup gateway connection if a bastion host is provided.
        gateway = None
        if self.bastion_host:
            gateway_connect_kwargs = {}
            if self.bastion_host_user_keyfile:
                gateway_connect_kwargs["key_filename"] = self.bastion_host_user_keyfile
            else:
                gateway_connect_kwargs["password"] = self.bastion_host_user_password

            # Connect to the bastion host.
            gateway = fabric.Connection(
                host=self.bastion_host,
                user=self.bastion_host_user,
                connect_kwargs=gateway_connect_kwargs,
            )

        with fabric.Connection(
            host=self.target_host,
            user=self.target_host_user,
            connect_kwargs=connect_args,
            gateway=gateway,
        ) as ssh:
            while True:
                llm_reply = self.query_llm(messages)
                log.warning("LLM reply was: %s", llm_reply)

                if is_llm_done(llm_reply):
                    log.critical("All done!")
                    return

                ssh_reply = self.handle_ssh_command(ssh, llm_reply)
                update_conversation(messages, llm_reply, ssh_reply)
                self.context_size_warning_check(messages)

    @log_function_call
    def handle_ssh_command(self, ssh: fabric.Connection, llm_reply: str) -> str:
        """
        Send the LLM reply to the server via SSH and get the server's response.

        Args:
            ssh (fabric.Connection): The active SSH connection.
            llm_reply (str): The reply from the LLM.

        Returns:
            str: The server's response.
        """
        ssh_reply = self.run_ssh_cmd(connection=ssh, command=llm_reply)
        log.warning("SSH reply was: %s", ssh_reply)

        if is_string_too_long(ssh_reply):
            ssh_reply = self.summarize_string(ssh_reply)

        return ssh_reply

    @log_function_call
    def main(self):
        """Initialize and run the job."""
        self.initialize()

        # Initialize the conversation messages.
        messages = self.initialize_messages()

        # Setup SSH connection parameters.
        connect_args = self.setup_ssh_connection_params()

        # Process the interaction loop.
        self.process_interaction_loop(messages, connect_args)


@log_function_call
def strip_eot_from_string(string: str) -> str:
    """
    Strip the <|eot_id|> from the end of the LLM response for more human-readable output.

    Args:
        string (str): The string you wish to strip the EOT from.

    Returns:
        str: The input string with <|eot_id|> stripped, if present.
    """
    eot_token = "<|eot_id|>"
    if string.endswith(eot_token):
        return string[: -len(eot_token)]
    return string


@log_function_call
def is_string_too_long(string: str, threshold: int = 1000) -> bool:
    """
    Determine if the given string is longer than a certain threshold.

    This helps us determine if LLM output needs to be summarized to reduce context size.

    Args:
        string (string): The input string to check.
        threshold (int): The input string will be checked if it's longer than the threshold length.
                         Default is 1000.

    Returns:
        bool: True if string is longer than the threshold, otherwise returns False.
    """
    if len(string) > threshold:
        return True
    return False


@log_function_call
def count_tokens(messages) -> int:
    """
    Count the number of LLM tokens in the provided dictionary of context.

    Uses the list of dictionaries inside the messages list and counts the tokens in the
    "content" key.

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
        int: The number of tokens.
    """
    content_string = " ".join(message["content"] for message in messages)

    encoding = tiktoken.encoding_for_model("gpt-4o")
    tokens = encoding.encode(content_string)

    num_tokens = len(tokens)
    return num_tokens


@log_function_call
def is_llm_done(llm_reply: str) -> bool:
    """
    Check if the LLM has finished with its objective.

    Args:
        llm_reply (str): The reply from the LLM to analyze to determine if it's finished with its
                         objective.

    Returns:
        bool: True if the LLM is finished, False otherwise.
    """
    if llm_reply == "DONE":
        return True
    return False


@log_function_call
def update_conversation(messages: list, llm_reply: str, ssh_reply: str) -> None:
    """
    Update the conversation messages with the LLM's reply and the server's response.

    Args:
        messages (list): The list of messages in the conversation.
        llm_reply (str): The reply from the LLM.
        ssh_reply (str): The server's response.
    """
    messages.append({"role": "assistant", "content": llm_reply})
    messages.append({"role": "user", "content": ssh_reply})
