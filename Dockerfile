FROM python:3.13-slim

WORKDIR /app
COPY ./ssherlock_runner/ssherlock_runner.py /app

RUN pip install --no-cache-dir -r requirements.txt
RUN pip uninstall django django-htmlmin gunicorn

CMD ["python", "/app/ssherlock_runner.py"]
