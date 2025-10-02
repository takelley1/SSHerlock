#!/usr/bin/env bash
#
# Run the SSHerlock Runner locally.

set -euo pipefail

# Standard environment setup (repo root + optional venv).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"
ssherlock::setup_environment

docker run --rm -e .env "ssherlock_runner:${SSHERLOCK_RUNNER_IMAGE_TAG:-1}"
