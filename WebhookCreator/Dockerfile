FROM python:3.12.3-alpine

WORKDIR /app

COPY CustomModules ./CustomModules
COPY main.py .
COPY __init__.py .
COPY requirements.txt .

ENV TERM xterm
ENV PYTHONUNBUFFERED 1

ARG TARGETPLATFORM
ARG BUILD_DATE
ARG COMMIT
ARG VERSION

RUN apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev libc-dev linux-headers rust cargo g++ && \
    python -m pip install --upgrade pip && \
    pip install --upgrade setuptools && \
    pip install -r requirements.txt && \
    apk del .build-deps && \
    find /usr/local \
    \( -type d -a -name test -o -name tests \) \
    -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
    -exec rm -rf '{}' + && \
    rm -rf /root/.cache/pip

LABEL maintainer="Discord: pika.pika.no.mi (970119359840284743)" \
      commit=$COMMIT \
      description="Discord bot for creating Webhooks." \
      release=$BUILD_DATE \
      version="1.8.4"

CMD ["python3", "main.py"]
