FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN apt update && apt install -y certbot wget curl docker.io && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
