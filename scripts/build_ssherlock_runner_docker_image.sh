#!/usr/bin/env bash
#
# Build a Docker image for the SSHerlock Runner.

set -euo pipefail

# Standard environment setup (repo root + optional venv).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"
ssherlock::setup_environment

rm -rfv "ssherlock_runner/docker"

# Create build directory.
mkdir "ssherlock_runner/docker"

# Copy files into build directory.
cp "Dockerfile" "ssherlock_runner/docker/Dockerfile"
cp "ssherlock_runner/ssherlock_runner.py" "ssherlock_runner/docker/ssherlock_runner.py"
grep -Ev "django|gunicorn" "requirements.txt" > "ssherlock_runner/docker/requirements.txt"

# Build the image.
cd "ssherlock_runner/docker" || exit 1
docker build -t "ssherlock_runner:${SSHERLOCK_RUNNER_IMAGE_TAG:-1}" .
docker image ls

# Cleanup.
cd -
rm -rf "ssherlock_runner/docker"
