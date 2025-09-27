#!/usr/bin/env bash
#
# Start the SSHerlock server in a test configuration.

set -euo pipefail

# Standard environment setup (repo root + optional venv).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"
ssherlock::setup_environment

cd ssherlock
python manage.py makemigrations ssherlock_server
python manage.py migrate
python manage.py runserver
