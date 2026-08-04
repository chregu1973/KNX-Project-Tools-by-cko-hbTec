FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN mkdir -p /data/sessions

EXPOSE 5000

CMD ["gunicorn", "-w", "1", "--threads", "4", "--timeout", "360", "--access-logfile", "-", "--error-logfile", "-", "--capture-output", "-b", "0.0.0.0:5000", "app:app"]
