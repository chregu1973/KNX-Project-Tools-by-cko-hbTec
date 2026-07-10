FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN mkdir -p /data/uploads /data/exports

EXPOSE 5000

CMD ["gunicorn", "-w", "1", "--timeout", "180", "-b", "0.0.0.0:5000", "app:app"]
