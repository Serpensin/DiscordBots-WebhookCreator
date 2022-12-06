FROM python:3.9.15-slim-bullseye
WORKDIR /app

COPY activity.json .
COPY WebhookCreator.py .
COPY requirements.txt .

RUN pip install -r requirements.txt

CMD ["python3", "WebhookCreator.py"]
