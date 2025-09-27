#!/usr/bin/env bash
# Common helper functions shared by SSHerlock scripts.

set -euo pipefail

ssherlock::goto_repo_root() {
  # Navigate to the root of the git repository.
  local repo_root
  if ! repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    printf "%s\n" "Error: Not inside a git repository." >&2
    exit 1
  fi
  cd "${repo_root}" || exit 1
}

ssherlock::activate_venv_if_available() {
  # Activate the Python virtual environment if not already active.
  if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    if [[ -f "./venv/bin/activate" ]]; then
      # shellcheck source=/dev/null
      source "./venv/bin/activate"
    fi
  fi
}

ssherlock::setup_environment() {
  # Perform standard script setup: ensure repo root and activate venv if present.
  ssherlock::goto_repo_root
  ssherlock::activate_venv_if_available
}
