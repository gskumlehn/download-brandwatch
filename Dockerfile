FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install OS deps if needed (add as required)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 8080

# Run with gunicorn; increase timeout to allow long downloads (e.g. 3600s)
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app", "--workers", "2", "--timeout", "3600"]
