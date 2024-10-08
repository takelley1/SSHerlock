#!/usr/bin/env bash
#
# Start the SSHerlock server in a test configuration.

set -euo pipefail

# Ensure we start at the root of the git repo.
cd "$(git rev-parse --show-toplevel)" || exit 1

# Enter the venv if we're not already in it.
if ! python --version &>/dev/null; then
    source ./venv/bin/activate
fi

cd ssherlock
python manage.py makemigrations ssherlock_server
python manage.py migrate
python manage.py runserver
