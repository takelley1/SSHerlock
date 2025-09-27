#!/usr/bin/env bash
# Run tests for all of the ssherlock server code.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

ssherlock::setup_environment

printf "%s\n" "############################################"
printf "%s\n" "####    RUNNING TESTS FOR DJANGO APP    ####"
printf "%s\n" "############################################"
cd ssherlock/tests || exit 1
coverage erase
coverage run --branch --source=../ssherlock_server ../manage.py test --force-color "$@"
coverage report --skip-covered --show-missing
