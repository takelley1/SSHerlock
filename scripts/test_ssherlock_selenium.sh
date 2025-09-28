#!/usr/bin/env bash
# Run Selenium end-to-end tests for the SSHerlock Django app.
# Usage:
#   scripts/test_selenium.sh [--browser chrome|firefox] [--headed] [--] [extra manage.py test args...]
#
# Examples:
#   scripts/test_selenium.sh
#   scripts/test_selenium.sh --browser firefox --headed -k SeleniumSSHerlockTests
#
# Environment variables:
#   SELENIUM_BROWSER  - chrome (default) or firefox
#   SELENIUM_HEADLESS - 1 (default) for headless, 0 for headed

set -euo pipefail

# Initialize optional extra args array to avoid unbound var with set -u
declare -a EXTRA_ARGS=()

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

usage() {
  printf "%s\n" "Run Selenium end-to-end tests."
  printf "%s\n" "Options:"
  printf "  %-24s %s\n" "--browser chrome|firefox" "Choose browser (default: chrome)"
  printf "  %-24s %s\n" "--headed" "Run with browser UI (disables headless)"
  printf "  %-24s %s\n" "--headless" "Force headless mode"
  printf "  %-24s %s\n" "--help" "Show this help"
  printf "%s\n" "All remaining args are passed to 'manage.py test'."
}

parse_args() {
  BROWSER="${SELENIUM_BROWSER:-chrome}"
  HEADLESS="${SELENIUM_HEADLESS:-1}"
  EXTRA_ARGS=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --browser)
        if [[ $# -lt 2 ]]; then
          printf "%s\n" "Error: --browser requires an argument." >&2
          exit 1
        fi
        BROWSER="$2"
        shift 2
        ;;
      --browser=*)
        BROWSER="${1#*=}"
        shift 1
        ;;
      --chrome)
        BROWSER="chrome"
        shift 1
        ;;
      --firefox)
        BROWSER="firefox"
        shift 1
        ;;
      --headed)
        HEADLESS="0"
        shift 1
        ;;
      --headless)
        HEADLESS="1"
        shift 1
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      --)
        shift
        while [[ $# -gt 0 ]]; do
          EXTRA_ARGS+=("$1")
          shift
        done
        ;;
      *)
        EXTRA_ARGS+=("$1")
        shift 1
        ;;
    esac
  done

  # Normalize values
  case "${BROWSER}" in
    chrome|firefox) ;;
    *)
      printf "%s\n" "Error: Unsupported browser '${BROWSER}'. Use 'chrome' or 'firefox'." >&2
      exit 1
      ;;
  esac
  case "${HEADLESS}" in
    0|1) ;;
    *)
      printf "%s\n" "Error: SELENIUM_HEADLESS must be 0 or 1." >&2
      exit 1
      ;;
  esac
}

main() {
  ssherlock::setup_environment

  if [[ ! -f "ssherlock/manage.py" ]]; then
    printf "%s\n" "Error: ssherlock/manage.py not found in repo root." >&2
    exit 1
  fi

  parse_args "$@"

  export SELENIUM_BROWSER="${BROWSER}"
  export SELENIUM_HEADLESS="${HEADLESS}"

  printf "%s\n" "==============================================="
  printf "%s\n" " Running Selenium tests"
  printf "%s\n" " Browser:  ${SELENIUM_BROWSER}"
  printf "%s\n" " Headless: ${SELENIUM_HEADLESS}"
  printf "%s\n" "==============================================="

  # Run only the selenium tests package to avoid running entire suite unless requested.
  python "ssherlock/manage.py" test ssherlock/tests/selenium_tests --pattern="selenium_*.py" -v 2 ${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}
}

main "$@"
