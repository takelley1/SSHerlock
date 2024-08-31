#!/usr/bin/env bash

# Ensure we start at the root of the git repo.
cd "$(git rev-parse --show-toplevel)" || exit 1

# Enter the venv if we're not already in it.
if ! python --version &>/dev/null; then
    source ./venv/bin/activate
fi

cd ssherlock/tests || exit 1
python ../manage.py test --shuffle $*
