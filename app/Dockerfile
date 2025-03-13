# Base stage
FROM python:3.9-slim-buster AS base

RUN apt-get update && apt-get -y install libpq-dev gcc

WORKDIR /usr/src

COPY ./requirements.txt /usr/src/requirements.txt

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# API stage
FROM base AS api

WORKDIR /usr/src/

# Copy only API-related files
# COPY ./api /usr/src/api
RUN ls /usr/src

# CMD ["python", "app.py", "run", "-h", "0.0.0.0:${PORT}"]

# Backend stage
FROM base AS backend

WORKDIR /usr/src/

# Copy only backend-related files
COPY ./backend /usr/src/backend

# CMD ["python", "worker.py"]