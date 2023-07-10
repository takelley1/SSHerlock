import logging as log
from flask import jsonify, request
import fabric
from . import main


@main.route("/ssh", methods=["POST"])
def execute_ssh():
    data = request.get_json()

    log.info("Data is: %s", data)

    host = data.get("host")
    log.info("Host = %s", host)

    user = data.get("user")
    log.info("User = %s", user)

    password = data.get("password")
    log.info("password = %s", password)

    command = data.get("command")
    log.info("Command = %s", command)

    if not host or not command or not user or not password:
        return jsonify({"error": "Invalid request"}), 400

    output = execute_ssh_command(host, user, password, command)
    log.info("Output is: \n%s", str(output))
    return jsonify(output)


def execute_ssh_command(host, user, password, command):
    c = fabric.Connection(
        host=host, user=user, connect_kwargs={"password": password}, port=22
    )
    result = c.run(command, hide=True, warn=True)
    output = {"stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    return output
