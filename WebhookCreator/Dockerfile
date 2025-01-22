FROM python:3.12-alpine

WORKDIR /app

COPY CustomModules ./CustomModules
COPY *.py .
COPY requirements.txt .

ENV TERM=xterm
ENV PYTHONUNBUFFERED=1

ARG TARGETPLATFORM
ARG BUILD_DATE
ARG COMMIT

RUN apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev libc-dev linux-headers rust cargo g++ && \
    apk add curl && \
    python -m pip install --root-user-action ignore  --upgrade pip && \
    pip install --root-user-action ignore  --upgrade setuptools && \
    pip install --root-user-action ignore  -r requirements.txt && \
    apk del .build-deps && \
    find /usr/local \
    \( -type d -a -name test -o -name tests \) \
    -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
    -exec rm -rf '{}' + && \
    rm -rf /root/.cache/pip

LABEL maintainer="Discord: pika.pika.no.mi (970119359840284743)" \
      description="Discord bot for creating Webhooks." \
      release=$BUILD_DATE \
      version="1.10.0"

CMD ["python3", "main.py"]
