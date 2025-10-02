"""Main worker that runs jobs created by the SSHerlock server."""

# pylint: disable=import-error
import os
import json
import logging as log
import time

import fabric
import openai
import requests
import tiktoken


SSHERLOCK_SERVER_DOMAIN = os.getenv(
    "SSHERLOCK_SERVER_DOMAIN", "host.docker.internal:8000"
)
SSHERLOCK_SERVER_PROTOCOL = os.getenv("SSHERLOCK_SERVER_PROTOCOL", "http")
SSHERLOCK_SERVER_RUNNER_TOKEN = os.getenv(
    "SSHERLOCK_SERVER_RUNNER_TOKEN", "myprivatekey"
)
SSHERLOCK_RUNNER_MAX_ATTEMPTS = int(os.getenv("SSHERLOCK_RUNNER_MAX_ATTEMPTS", "3"))
SSHERLOCK_RUNNER_LOG_LEVEL = os.getenv("SSHERLOCK_RUNNER_LOG_LEVEL", "DEBUG").upper()
SSHERLOCK_LLM_MODEL = os.getenv("SSHERLOCK_LLM_MODEL", "llama3.1")
SSHERLOCK_TOKEN_ENCODING_MODEL = os.getenv("SSHERLOCK_TOKEN_ENCODING_MODEL", "gpt-4o")


class HttpPostHandler(log.Handler):
    """Custom logging handler to send logs to the SSHerlock server via HTTP POST."""

    def __init__(self, job_id):
        """Initialize the HttpPostHandler with a job ID."""
        super().__init__()
        self.job_id = job_id

    def emit(self, record):
        """Emit a log record to the SSHerlock server."""
        log_entry = self.format(record)
        try:
            response = requests.post(
                f"{SSHERLOCK_SERVER_PROTOCOL}://{SSHERLOCK_SERVER_DOMAIN}/log_job_data/{self.job_id}",
                headers={
                    "Authorization": f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}",
                    "Content-Type": "application/json",
                },
                data=json.dumps({"log": log_entry}),
                timeout=10,
            )
            if response.status_code != 200:
                print(f"Failed to send log entry: {response.content}")
        except Exception as e:
            print(f"Error sending log entry: {e}")


log.basicConfig(
    level=getattr(log, SSHERLOCK_RUNNER_LOG_LEVEL, log.DEBUG),
    format="%(asctime)s %(levelname)s %(filename)s:%(funcName)s - %(message)s",
)


def update_job_status(job_id, status):
    """Update the status of a job via an API call.

    Args:
        job_id (str): The ID of the job.
        status (str): The new status of the job.

    Returns:
        None
    """
    try:
        log.debug("Updating job %s status to %s", job_id, status)
        response = requests.post(
            f"{SSHERLOCK_SERVER_PROTOCOL}://{SSHERLOCK_SERVER_DOMAIN}/update_job_status/{job_id}",
            headers={
                "Authorization": f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}",
                "Content-Type": "application/json",
            },
            data=json.dumps({"status": status}),
            timeout=10,
        )
        if response.status_code != 200:
            log.error(
                "Failed to update job %s status to %s. Status code: %d. Output: %s",
                job_id,
                status,
                response.status_code,
                response.content,
            )
    except Exception as e:
        log.error("Error updating job status for job %s: %s", job_id, str(e))


def run_job(job_data):
    """Execute a job based on the provided job data.

    Args:
        job_data (dict): Dictionary containing job information including id, API base URL,
                            instructions, target host details, and credentials.
    """
    http_post_handler = HttpPostHandler(job_data["id"])
    http_post_handler.setLevel(log.INFO)  # Set desired level for remote logging

    try:
        # Start sending log messages to the server when the job starts.
        log.getLogger().addHandler(http_post_handler)

        log.info("Running job: %s", job_data["id"])
        runner = Runner(
            job_id=job_data["id"],
            llm_api_base_url=job_data["llm_api_baseurl"],
            initial_prompt=job_data["instructions"],
            target_host_hostname=job_data["target_host_hostname"],
            credentials_for_target_hosts_username=job_data[
                "credentials_for_target_hosts_username"
            ],
            llm_api_api_key=job_data["llm_api_api_key"],
            credentials_for_target_hosts_password=job_data[
                "credentials_for_target_hosts_password"
            ],
            bastion_host_hostname=job_data["bastion_host_hostname"],
            credentials_for_bastion_host_username=job_data[
                "credentials_for_bastion_host_username"
            ],
            credentials_for_bastion_host_password=job_data[
                "credentials_for_bastion_host_password"
            ],
        )
        runner.run()
        log.info("Job %s completed", job_data["id"])
    except Exception as e:
        log.error("Error running job: %s", e)
        log.getLogger().removeHandler(http_post_handler)


def request_job():
    """Fetch the next available job from the API.

    Returns:
        dict: A dictionary containing job details if available, otherwise None.
    """
    try:
        response = requests.get(
            f"{SSHERLOCK_SERVER_PROTOCOL}://{SSHERLOCK_SERVER_DOMAIN}/request_job",
            timeout=60,
            headers={"Authorization": f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}"},
        )
        if response.status_code == 200:
            return response.json()
        log.warning(
            "No pending jobs found: (%d) %s", response.status_code, response.content
        )
        return None
    except Exception as e:
        log.error("Error fetching job: %s", e)
        return None


class Runner:  # pylint: disable=too-many-arguments
    """Main class for runner configuration."""

    def __init__(
        self,
        job_id,
        llm_api_base_url,
        initial_prompt,
        target_host_hostname,
        credentials_for_target_hosts_username,
        llm_api_api_key="Bearer no-key",
        model_context_size=0,
        log_level="WARNING",
        credentials_for_target_hosts_password="",
        credentials_for_target_hosts_keyfile="",
        credentials_for_target_hosts_sudo_password="",
        bastion_host_hostname="",
        credentials_for_bastion_host_username="",
        credentials_for_bastion_host_password="",
        credentials_for_bastion_host_keyfile="",
    ):
        """Initialize main runner configuration."""
        self.job_id = job_id
        self.log_level = log_level
        self.initial_prompt = initial_prompt
        self.model_context_size = model_context_size
        self.target_host_hostname = target_host_hostname
        self.credentials_for_target_hosts_username = (
            credentials_for_target_hosts_username
        )
        self.credentials_for_target_hosts_password = (
            credentials_for_target_hosts_password
        )
        self.credentials_for_target_hosts_keyfile = credentials_for_target_hosts_keyfile
        self.credentials_for_target_hosts_sudo_password = (
            credentials_for_target_hosts_sudo_password
        )
        self.bastion_host_hostname = bastion_host_hostname
        self.credentials_for_bastion_host_username = (
            credentials_for_bastion_host_username
        )
        self.credentials_for_bastion_host_password = (
            credentials_for_bastion_host_password
        )
        self.credentials_for_bastion_host_keyfile = credentials_for_bastion_host_keyfile
        self.llm_api_base_url = llm_api_base_url
        self.llm_api_api_key = llm_api_api_key
        self.shell_environment = (
            "DEBIAN_FRONTEND=noninteractive SYSTEMD_PAGER='' EDITOR='' PAGER=''"
        )
        self.system_prompt = (
            "You're an autonomous system administrator managing a server non-interactively."
            "Your objective is print the next command to run to complete the task and NOTHING ELSE!"
            "You MUST FOLLOW ALL OF THESE RULES EXACTLY!!!"
            "1. If your objective has been completed successfully, print DONE"
            "2. Prepend privileged actions with sudo!"
            "3. Don't use tools that require interaction with the terminal, like vim or nano!"
            "4. Don't include explanations of anything, only print commands!"
            "5. Don't print multiple commands at one time!"
            "6. Add -y to package installation commands!"
            "7. If you get errors of any kind, try a different command!"
            "8. Don't do anything that could break the system!"
            "9. If using a package installation command, ensure the output is quiet and stdout is limited."
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

    def initialize(self) -> None:
        """Run general setup and safety checks."""
        if not self.can_target_server_be_reached():
            log.critical("Can't reach target server!")
            raise RuntimeError
        self.wait_for_llm_to_become_available()

    def query_llm(self, prompt) -> str:
        """Send a prompt to an LLM API and return its reply.

        LLM API must be OpenAI-compatible.

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
            api_key=self.llm_api_api_key,
        )

        llm_reply = client.chat.completions.create(
            model=SSHERLOCK_LLM_MODEL,
            messages=prompt,
        )

        response_string = llm_reply.choices[0].message.content
        response_string_stripped = strip_eot_from_string(response_string)
        return response_string_stripped

    def can_llm_be_reached(self) -> bool:
        """Check if the LLM API can be reached with a quick prompt.

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
        except (openai.InternalServerError, openai.APITimeoutError):
            return False

    def can_target_server_be_reached(self) -> bool:
        """Check if the target server can be reached via SSH.

        Returns:
            bool: True if the server can be reached, False otherwise.
        """
        log.warning("Checking target server reachability...")
        try:
            connect_args = self.setup_ssh_connection_params()
            with fabric.Connection(
                host=self.target_host_hostname,
                user=self.credentials_for_target_hosts_username,
                connect_kwargs=connect_args,
                connect_timeout=30,
            ) as ssh:
                ssh.run("echo 'Server is reachable'", hide=True)
            return True
        except Exception as e:
            log.error("Failed to reach the target server: %s", str(e))
            update_job_status(self.job_id, "Failed")
            return False

    def wait_for_llm_to_become_available(self) -> None:
        """Wait until the LLM API can be reached successfully.

        Raises:
            Raises a RuntimeError if waiting times out.
        """
        log.warning("Checking LLM connectivity...")
        for i in range(1, 100):
            if self.can_llm_be_reached() is False:
                log.warning("Waiting for LLM server to become available ... %s/100", i)
                time.sleep(10)
            else:
                return
        update_job_status(self.job_id, "Failed")
        raise RuntimeError("Timed out waiting for LLM server to become available!")

    def summarize_string(self, string: str) -> str:
        """Summarize the given string with the LLM API.

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

    def context_size_warning_check(self, messages, threshold=0.85) -> bool:
        """Print a warning if we're about to exceed the context size of the model.

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
            return False
        num_tokens = count_tokens(messages)
        log.warning("Currently using %s tokens", num_tokens)
        if num_tokens > (threshold * self.model_context_size):
            log.warning("REACHED %s OF MODEL CONTEXT SIZE", str(threshold))
            return True
        return False

    def run_ssh_cmd(self, connection: fabric.Connection, command: str) -> str:
        """Run a command over an existing SSH connection and return its output.

        Args:
            ssh (fabric.Connection): The open SSH connection to use for command execution.
            command (str): The command to run on the host.
            sudo_password (str): The password to use to elevate with sudo.

        Returns:
            str: SSH command output. Both stdout and stderr are combined into a single string.
        """
        command = f"{self.shell_environment} ; {command}"

        try:
            # Set pty=False to prevent interactive commands.
            # Set hide="both" to prevent echoing stdout and stderr.
            if self.credentials_for_target_hosts_sudo_password:
                result = connection.sudo(
                    command,
                    warn=True,
                    pty=False,
                    password=self.credentials_for_target_hosts_sudo_password,
                    hide="both",
                )
            else:
                result = connection.run(command, warn=True, pty=False, hide="both")

            # Combine output streams for the LLM.
            output = result.stdout.strip() + result.stderr.strip()
            log.debug("run_ssh_cmd output is: %s", output)
            return output
        except Exception as e:
            log.error("SSH command failed: %s", e)
            update_job_status(self.job_id, "Failed")
            raise

    def is_job_canceled(self) -> bool:
        """Call the SSHerlock server API to get the current status of the job.

        Returns:
            bool: True if the job is canceled, False otherwise.
        """
        try:
            response = requests.get(
                f"{SSHERLOCK_SERVER_PROTOCOL}://{SSHERLOCK_SERVER_DOMAIN}/job_status",
                headers={"Authorization": f"Bearer {SSHERLOCK_SERVER_RUNNER_TOKEN}"},
                timeout=5,
            )
            response.raise_for_status()
            status = response.json().get("status")
            if status == "Canceled":
                return True
            return False
        except requests.RequestException as e:
            log.error("Error checking job status: %s", str(e))
            return False

    def initialize_messages(self) -> list:
        """Initialize the messages list with the system and user prompts.

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

    def setup_ssh_connection_params(self) -> dict:
        """Prepare SSH connection parameters based on the configuration.

        Args:
            config (Config): Configuration object containing SSH credentials.

        Returns:
            dict: SSH connection parameters.
        """
        if self.credentials_for_target_hosts_keyfile:
            return {"key_filename": self.credentials_for_target_hosts_keyfile}
        return {"password": self.credentials_for_target_hosts_password}

    def process_interaction_loop(self, messages: list, connect_args: dict) -> None:
        """Process the interaction loop with the LLM and SSH server.

        Args:
            messages (list): The list of messages in the conversation.
            connect_args (dict): SSH connection parameters.
        """
        # Setup gateway connection if a bastion host is provided.
        gateway = None
        if self.bastion_host_hostname:
            gateway_connect_kwargs = {}
            if self.credentials_for_bastion_host_keyfile:
                gateway_connect_kwargs["key_filename"] = (
                    self.credentials_for_bastion_host_keyfile
                )
            else:
                gateway_connect_kwargs["password"] = (
                    self.credentials_for_bastion_host_password
                )

            # Connect to the bastion host.
            gateway = fabric.Connection(
                host=self.bastion_host_hostname,
                user=self.credentials_for_bastion_host_username,
                connect_kwargs=gateway_connect_kwargs,
            )

        with fabric.Connection(
            host=self.target_host_hostname,
            user=self.credentials_for_target_hosts_username,
            connect_kwargs=connect_args,
            gateway=gateway,
        ) as ssh:
            update_job_status(self.job_id, "Running")
            while True:
                llm_reply = self.query_llm(messages)
                log.warning("LLM reply was: %s", llm_reply)

                if is_llm_done(llm_reply):
                    log.critical("All done!")
                    update_job_status(self.job_id, "Completed")
                    return

                if self.is_job_canceled():
                    log.critical("Job canceled!")
                    update_job_status(self.job_id, "Canceled")
                    return

                ssh_reply = self.handle_ssh_command(ssh, llm_reply)
                update_conversation(messages, llm_reply, ssh_reply)
                self.context_size_warning_check(messages)

    def handle_ssh_command(self, ssh: fabric.Connection, llm_reply: str) -> str:
        """Send the LLM reply to the server via SSH and get the server's response.

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

    def run(self):
        """Initialize and run the job."""
        try:
            self.initialize()
        except RuntimeError as e:
            raise e

        # Initialize the conversation messages.
        messages = self.initialize_messages()

        # Setup SSH connection parameters.
        connect_args = self.setup_ssh_connection_params()

        # Process the interaction loop.
        self.process_interaction_loop(messages, connect_args)


def strip_eot_from_string(string: str) -> str:
    """Strip the <|eot_id|> from the end of the LLM response for more human-readable output.

    Args:
        string (str): The string you wish to strip the EOT from.

    Returns:
        str: The input string with <|eot_id|> stripped, if present.
    """
    eot_token = "<|eot_id|>"
    if string.endswith(eot_token):
        return string[: -len(eot_token)]
    return string


def is_string_too_long(string: str, threshold: int = 1000) -> bool:
    """Determine if the given string is longer than a certain threshold.

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


def count_tokens(messages) -> int:
    """Count the number of LLM tokens in the provided dictionary of context.

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

    encoding = tiktoken.encoding_for_model(SSHERLOCK_TOKEN_ENCODING_MODEL)
    tokens = encoding.encode(content_string)

    num_tokens = len(tokens)
    return num_tokens


def is_llm_done(llm_reply: str) -> bool:
    """Check if the LLM has finished with its objective.

    Args:
        llm_reply (str): The reply from the LLM to analyze to determine if it's finished with its
                         objective.

    Returns:
        bool: True if the LLM is finished, False otherwise.
    """
    if llm_reply == "DONE":
        return True
    return False


def update_conversation(messages: list, llm_reply: str, ssh_reply: str) -> None:
    """Update the conversation messages with the LLM's reply and the server's response.

    Args:
        messages (list): The list of messages in the conversation.
        llm_reply (str): The reply from the LLM.
        ssh_reply (str): The server's response.
    """
    messages.append({"role": "assistant", "content": llm_reply})
    messages.append({"role": "user", "content": ssh_reply})


def fetch_job_data(attempt, max_attempts):
    """Fetch job data by requesting jobs until one is available or attempts are exhausted.

    Args:
        attempt (int): Current attempt count.
        max_attempts (int or None): Maximum number of attempts allowed.

    Returns:
        dict or None: Job data if available, otherwise None.
    """
    if max_attempts is None:
        max_attempts = SSHERLOCK_RUNNER_MAX_ATTEMPTS
    while True:
        if max_attempts is not None and attempt >= max_attempts:
            log.info("Maximum attempts reached. Ceasing operation.")
            return None

        try:
            job_data = request_job()
            if job_data:
                return job_data
            log.info("Runner: waiting for a job...%s", attempt + 1)
            time.sleep(3)
        except Exception as e:
            log.error("Runner: error requesting job: %s", str(e))
            log.info("Retrying to fetch job...")
            time.sleep(3)

        attempt += 1


def execute_job(job_data):
    """Execute the given job and handle any exceptions.

    Args:
        job_data (dict): The job data to be processed.
    """
    try:
        run_job(job_data)
    except Exception as e:
        log.error("Job failed with error: %s", str(e))
        log.info("Continuing to wait for new jobs...")


def main(max_attempts=25):
    """Main loop to continually request a job to run and run any job it receives.

    Args:
        max_attempts (int, optional): Maximum attempts to wait for a job. Defaults to None.
    """
    attempt = 0

    log.info("Starting runner")
    while True:
        job_data = fetch_job_data(attempt, max_attempts)
        if job_data is None:
            return

        execute_job(job_data)


if __name__ == "__main__":
    main()
