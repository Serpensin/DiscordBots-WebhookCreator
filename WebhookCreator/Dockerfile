FROM python:3.9.16-slim-bullseye

WORKDIR /app

COPY main.py .
COPY requirements.txt .
COPY activity.json .

RUN apt-get update \
    && apt-get install -y build-essential libssl-dev libffi-dev python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN python -m pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt

CMD ["python3", "main.py"]
