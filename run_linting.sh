#!/usr/bin/env bash
#
# Run linting on this repo.

# Ensure we start at the root of the git repo.
cd "$(git rev-parse --show-toplevel)" || exit 1

# Enter the venv if we're not already in it.
if ! python --version &>/dev/null; then
    source ./venv/bin/activate
fi

echo "############################################"
echo "####    RUNNING CODESPELL               ####"
echo "############################################"
codespell -S "./venv/*,*ansible*.j2"

echo "############################################"
echo "####    RUNNING YAMLLINT                ####"
echo "############################################"
yamllint --config-file ./conf/.yamllint .

echo "############################################"
echo "####    RUNNING FLAKE8                  ####"
echo "############################################"
flake8 --conf ./conf/.flake8rc $(git ls-files '*.py')

echo "############################################"
echo "####    RUNNING PYLINT                  ####"
echo "############################################"
pylint --rcfile=./conf/.pylintrc $(git ls-files '*.py')

echo "############################################"
echo "####    RUNNING PYDOCSTYLE              ####"
echo "############################################"
pydocstyle --config=./conf/.pydocstyle