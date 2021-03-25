#!/usr/bin/env bash

pyenv local 3.6.2

export AWS_DEFAULT_REGION='us-east-1'

pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r tests/requirements.txt

FLAKE8_OPTIONS="app.py chalicelib/ tests/"
flake8 ${FLAKE8_OPTIONS}

if [[ $? > 0 ]]; then
    echo "PEP8 violations detected!"
    exit 1
fi

NOSE_OPTIONS="-v \
    --failure-detail \
    --cover-html \
    --cover-html-dir=htmlcov \
    --cover-min-percentage=93 \
    --with-coverage \
    --cover-erase \
    --cover-branches \
    --cover-package=app --cover-package=chalicelib \
    --cover-inclusive \
    --with-xunit"

nosetests ${NOSE_OPTIONS} tests/unit
