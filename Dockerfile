FROM docker.io/python:3.11

WORKDIR /usr/src/app

COPY requirements/base.txt requirements.txt

RUN pip install --no-cache-dir --requirement requirements.txt

COPY src ./src
COPY setup.py .

RUN pip install --editable .
