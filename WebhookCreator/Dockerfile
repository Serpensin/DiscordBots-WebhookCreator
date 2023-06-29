FROM python:3.9.16-alpine

WORKDIR /app

COPY *.py .
COPY requirements.txt .

ENV TERM xterm
ENV PYTHONUNBUFFERED 1

ARG TARGETPLATFORM
ARG BUILD_DATE
ARG COMMIT
ARG VERSION

RUN python -m pip install --upgrade pip && \
    pip install --upgrade setuptools && \
    if [ "$TARGETPLATFORM" = "linux/arm/v6" ] || [ "$TARGETPLATFORM" = "linux/arm/v7" ]; then \
        apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev; \
    fi && \
    pip install -r requirements.txt && \
    if [ "$TARGETPLATFORM" = "linux/arm/v6" ] || [ "$TARGETPLATFORM" = "linux/arm/v7" ]; then \
        apk del .build-deps; \
    fi && \
    find /usr/local \
    \( -type d -a -name test -o -name tests \) \
    -o \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
    -exec rm -rf '{}' + && \
    rm -rf /root/.cache/pip

LABEL maintainer="Discord: the_devil_of_the_rhine (863687441809801246)" \
      commit=$COMMIT \
      description="Discord bot for creating Webhooks." \
      release=$BUILD_DATE \
      version=$VERSION

CMD ["python3", "main.py"]
