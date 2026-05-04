# ============================================================
# Dockerfile — finai-agent-api (Python/FastAPI)
# Letakkan file ini di: finai-agent/Dockerfile
# ============================================================

FROM python:3.13-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements dulu (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

EXPOSE 8100

CMD ["python", "api.py"]
