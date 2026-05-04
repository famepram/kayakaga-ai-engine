FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create .env file if it doesn't exist (for development)
RUN if [ ! -f .env ]; then \
    echo "OPENROUTER_API_KEY=\nOPENAI_BASE_URL=https://openrouter.ai/api/v1\nMODEL=google/gemma-4-31b-it:free\nFINAI_API_URL=http://kayakaga-api:8080\nAGENT_PORT=8000\nAGENT_HOST=0.0.0.0\nKAYAKAGA_API_URL=http://kayakaga-api:8080" > .env; \
    fi

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
