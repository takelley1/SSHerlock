#!/usr/bin/env bash
# Run tests for all of the ssherlock runner code.
set -euo pipefail

# Standard environment setup (repo root + optional venv).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"
ssherlock::setup_environment

printf "%s\n" "############################################"
printf "%s\n" "####      RUNNING TESTS FOR RUNNER      ####"
printf "%s\n" "############################################"
cd ssherlock_runner/tests || exit 1
coverage erase
coverage run --branch --source=ssherlock_runner -m pytest -v .
coverage report --show-missing
