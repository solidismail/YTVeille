FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir \
    "fastapi>=0.110.0" \
    "uvicorn[standard]>=0.29.0" \
    "httpx>=0.27.0" \
    "pydantic>=2.6.0" \
    "apscheduler>=3.10.4"

COPY . .

CMD ["python", "worker/scheduler.py"]
