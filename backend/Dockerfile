# FROM python:3.10-slim can't install all python packages. Use image without slim
FROM python:3.10

RUN mkdir /app

RUN apt update \
  && pip3 install --upgrade pip \
  && pip3 install poetry==1.1.12

COPY poetry.lock pyproject.toml /app

WORKDIR /app

# Do we need install development dependencies
ARG DEV_DEPS=False

RUN poetry config virtualenvs.create false
RUN if [ $DEV_DEPS = True ] ; then poetry install --no-interaction --no-ansi ; else poetry install --no-dev --no-interaction --no-ansi ; fi

COPY ./docker-entrypoint.sh /app/docker-entrypoint.sh
COPY . /app

WORKDIR /app

ENTRYPOINT ["sh", "./docker-entrypoint.sh"]
