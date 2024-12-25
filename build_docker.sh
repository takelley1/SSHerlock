#!/usr/bin/env bash
#
# Build a Docker image for the SSHerlock Runner.
set -euo pipefail

# Ensure we start at the root of the git repo.
cd "$(git rev-parse --show-toplevel)" || exit 1

# Enter the venv if we're not already in it.
if ! python --version &>/dev/null; then
    source ./venv/bin/activate
fi

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
