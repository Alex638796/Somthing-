# Clean & stable Dockerfile for Render
FROM python:3.11-slim-bookworm

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create sessions folder
RUN mkdir -p sessions

# Run the supervisor (Gunicorn health-check + Bot)
CMD ["python3", "run.py"]
