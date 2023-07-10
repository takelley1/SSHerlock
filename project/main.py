import logging as log
import flask
import flask_login
import flask_sqlalchemy
import fabric
from . import db

log.basicConfig(format="%(asctime)s %(funcName)s: %(message)s", level="INFO")

main = flask.Blueprint('main', __name__)

def execute_ssh_command(host, user, password, command):
    c = fabric.Connection(host=host, user=user, connect_kwargs={'password': password}, port=22)
    result = c.run(command, hide=True, warn=True)
    output = {"stdout": result.stdout.strip(),
              "stderr": result.stderr.strip()}
    return output

@main.route('/')
def index():
    return flask.render_template('index.html')

@main.route('/profile')
def profile():
    return flask.render_template('profile.html')


@main.route("/ssh", methods=["POST"])
def execute_ssh():
    data = flask.request.get_json()

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
        return flask.jsonify({"error": "Invalid request"}), 400

    output = execute_ssh_command(host, user, password, command)
    log.info("Output is: \n%s", str(output))
    return flask.jsonify(output)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
