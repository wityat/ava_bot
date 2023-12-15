FROM python:3.10.10 AS base


ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_NO_CACHE_DIR=off
ENV PYTHONDONTWRITEBYTECODE=on
ENV PYTHONFAULTHANDLER=on
ENV PYTHONUNBUFFERED=on
ENV PYTHONPATH=/opt/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /opt/app
WORKDIR /opt/app

COPY requirements.txt /opt/app/

RUN pip install -r requirements.txt

COPY tg_bot /opt/app/tg_bot

COPY alembic /opt/app/alembic
COPY Makefile /opt/app
COPY alembic.ini /opt/app

CMD ["python", "tg_bot"]
