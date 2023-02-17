FROM python:3.9.16-slim-bullseye
WORKDIR /app

COPY activity.json .
COPY main.py .
COPY requirements.txt .

RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python3", "main.py"]
