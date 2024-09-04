#!/usr/bin/env bash

# Ensure we start at the root of the git repo.
cd "$(git rev-parse --show-toplevel)" || exit 1

# Enter the venv if we're not already in it.
if ! python --version &>/dev/null; then
    source ./venv/bin/activate
fi

echo "############################################"
echo "####    RUNNING TESTS FOR DJANGO APP    ####"
echo "############################################"
cd ssherlock/tests || exit 1
coverage erase
coverage run --branch --source=../ssherlock_server ../manage.py test --shuffle --force-color $*
coverage report --skip-covered --show-missing

echo "############################################"
echo "####      RUNNING TESTS FOR RUNNER      ####"
echo "############################################"
cd - || exit 1
cd ssherlock_runner/tests || exit 1
coverage erase
coverage run --branch --source=ssherlock_runner -m pytest -v .
coverage report --show-missing
