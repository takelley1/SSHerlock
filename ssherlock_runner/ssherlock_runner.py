"""Main runner."""
# pylint: disable=import-error
import json
import logging as log
import multiprocessing
import sys
import time
from queue import Empty

import fabric
import openai
import requests
import tiktoken


# TODO: add debug logging for more processes
# TODO: complete test coverage for runner code

MAX_RUNNERS = 10

SSHERLOCK_SERVER_DOMAIN = "localhost:8000"
SSHERLOCK_SERVER_PROTOCOL = "http"
SSHERLOCK_SERVER_RUNNER_TOKEN = "myprivatekey"


log.basicConfig(
    level=log.DEBUG, format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s"
)


def update_job_status(job_id, status):
    """
    Update the status of a job via an API call.

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
    """
    Execute a job using the provided job data.

    Args:
        job_data (dict): A dictionary containing job details.

    Returns:
        None
    """
    job_id = job_data["id"]

    update_job_status(job_id, "RUNNING")
    log.info("Running job: %s", job_id)

    runner = Runner(
        job_id=job_data["job_id"],
        llm_api_base_url=job_data["llm_api_baseurl"],
        initial_prompt=job_data["instructions"],
        target_host=job_data["target_host_hostname"],
        target_host_user=job_data["credentials_for_target_hosts_username"],
        llm_api_key=job_data["llm_api_api_key"],
        target_host_user_password=job_data["credentials_for_target_hosts_password"],
        bastion_host=job_data["bastion_host_hostname"],
        bastion_host_user=job_data["credentials_for_bastion_host_username"],
        bastion_host_user_password=job_data["credentials_for_bastion_host_password"],
    )
    runner.run()
    update_job_status(job_id, "COMPLETED")
    log.info("Job %s completed", job_id)


def get_next_job():
    """
    Fetch the next available job from the API.

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


def launch_runner(job_queue):
    """
    Worker process that continuously processes jobs from the job queue.

    Args:
        job_queue (multiprocessing.JoinableQueue): The queue from which to fetch jobs.

    Returns:
        None
    """
    while True:
        try:
            job_data = job_queue.get(timeout=10)
            run_job(job_data)
            job_queue.task_done()
        except Empty:
            log.info("No job available. Exiting runner.")
            break


def job_manager():
    """
    Manage job processing by spawning worker processes and fetching jobs from the API.

    Returns:
        None
    """
    job_queue = multiprocessing.JoinableQueue()

    # List to track active runner processes
    active_runners = []

    try:
        while True:
            # Check if there are available jobs and not exceeding max runners
            if len(active_runners) < MAX_RUNNERS:
                log.debug("Retrieving next job...")
                job_data = get_next_job()

                if job_data:
                    log.debug("Got job data")
                    job_queue.put(job_data)
                    log.debug("Spawning runner worker")
                    p = multiprocessing.Process(target=launch_runner, args=(job_queue,))
                    log.debug("Starting worker runner")
                    p.start()
                    log.debug("Adding worker runners to runner list")
                    active_runners.append(p)

            for p in active_runners:
                log.debug("Cleaning up finished runners")
                if not p.is_alive():
                    active_runners.remove(p)

            # Throttle the job manager loop.
            time.sleep(3)

    except KeyboardInterrupt:
        log.info("Shutting down job manager...")
    finally:
        # Clean up all runners
        log.debug("Cleaning up finished runners")
        for p in active_runners:
            p.join()


class Runner:  # pylint: disable=too-many-arguments
    """Main class for runner configuration."""

    def __init__(
        self,
        job_id,
        llm_api_base_url,
        initial_prompt,
        target_host,
        target_host_user,
        llm_api_key="Bearer no-key",
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
        self.job_id = job_id
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
            update_job_status(self.job_id, "FAILED")
            sys.exit(1)
        self.wait_for_llm_to_become_available()

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
        except (openai.InternalServerError, openai.APITimeoutError):
            return False

    def can_target_server_be_reached(self) -> bool:
        """
        Check if the target server can be reached via SSH.

        Returns:
            bool: True if the server can be reached, False otherwise.
        """
        log.warning("Checking target server connectivity...")
        try:
            connect_args = self.setup_ssh_connection_params()
            with fabric.Connection(
                host=self.target_host,
                user=self.target_host_user,
                connect_kwargs=connect_args,
                connect_timeout=30,
            ) as ssh:
                ssh.run("echo 'Server is reachable'", hide=True)
            return True
        except Exception as e:
            log.error("Failed to reach the target server: %s", e)
            return False

    def wait_for_llm_to_become_available(self) -> None:
        """
        Wait in a loop until the LLM API can be reached successfully.

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
        raise RuntimeError("Timed out waiting for LLM server to become available!")

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
            return False
        num_tokens = count_tokens(messages)
        log.warning("Currently using %s tokens", num_tokens)
        if num_tokens > (threshold * self.model_context_size):
            log.warning("REACHED %s OF MODEL CONTEXT SIZE", str(threshold))
            return True
        return False

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

        # Set pty=False to prevent interactive commands.
        # Set hide="both" to prevent echoing stdout and stderr.
        if self.target_host_user_sudo_password:
            result = connection.sudo(
                command,
                warn=True,
                pty=False,
                password=self.target_host_user_sudo_password,
                hide="both",
            )
        else:
            result = connection.run(command, warn=True, pty=False, hide="both")

        # Combine output streams for the LLM.
        output = result.stdout.strip() + result.stderr.strip()
        log.debug("run_ssh_cmd output is: %s", output)
        return output

    def is_job_canceled(self) -> bool:
        """
        Call the SSHerlock server API to get the current status of the job.

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
            if status == "CANCELED":
                return True
            return False
        except requests.RequestException as e:
            log.error("Error checking job status: %s", e)
            return False

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

                if self.is_job_canceled():
                    log.critical("Job canceled!")
                    return

                ssh_reply = self.handle_ssh_command(ssh, llm_reply)
                update_conversation(messages, llm_reply, ssh_reply)
                self.context_size_warning_check(messages)

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

    def run(self):
        """Initialize and run the job."""
        self.initialize()

        # Initialize the conversation messages.
        messages = self.initialize_messages()

        # Setup SSH connection parameters.
        connect_args = self.setup_ssh_connection_params()

        # Process the interaction loop.
        self.process_interaction_loop(messages, connect_args)


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


if __name__ == "__main__":
    job_manager()
