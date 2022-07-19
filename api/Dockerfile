FROM python:3.9-slim-buster

RUN apt-get update && apt-get -y install libpq-dev gcc

WORKDIR /usr/src

COPY ./requirements.txt /usr/src/requirements.txt

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install python dependencies
# RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . /usr/src

# gunicorn
#CMD ["gunicorn", "--config", "gunicorn-cfg.py", "run:app"]
CMD python app.py run -h 0.0.0.0:${PORT}
