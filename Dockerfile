FROM python:3.12.3-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install deps first to leverage layer caching; avoid bytecode compilation for smaller size
COPY ./requirements_runner.txt /tmp/requirements_runner.txt
RUN python -m pip install --no-cache-dir --no-compile -r /tmp/requirements_runner.txt

# Copy only the runner script needed at runtime
COPY ./ssherlock_runner.py /app/ssherlock_runner.py

CMD ["python", "/app/ssherlock_runner.py"]
