FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system api && adduser --system --ingroup api api

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .
RUN mkdir -p /app/instance && chown -R api:api /app

USER api
EXPOSE 5000

CMD ["sh", "-c", "flask --app run.py db upgrade && gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 wsgi:app"]
