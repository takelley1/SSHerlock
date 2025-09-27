#!/usr/bin/env bash
#
# Run linting on this repo.
set -euo pipefail

# Standard environment setup (repo root + optional venv).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"
ssherlock::setup_environment


printf "%s\n" "############################################"
printf "%s\n" "####    RUNNING CODESPELL               ####"
printf "%s\n" "############################################"
codespell --skip "./venv/*,*ansible*.j2,./node_modules" --ignore-words-list "assertIn,ure"

printf "%s\n" "############################################"
printf "%s\n" "####    RUNNING YAMLLINT                ####"
printf "%s\n" "############################################"
yamllint --config-file ./conf/.yamllint $(git ls-files '*.yml')

printf "%s\n" "############################################"
printf "%s\n" "####    RUNNING FLAKE8                  ####"
printf "%s\n" "############################################"
flake8 --conf ./conf/.flake8rc $(git ls-files '*.py')

printf "%s\n" "############################################"
printf "%s\n" "####    RUNNING PYLINT                  ####"
printf "%s\n" "############################################"
pylint --rcfile=./conf/.pylintrc $(git ls-files '*.py')

printf "%s\n" "############################################"
printf "%s\n" "####    RUNNING PYDOCSTYLE              ####"
printf "%s\n" "############################################"
pydocstyle --config=./conf/.pydocstyle $(git ls-files)
