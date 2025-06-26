# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Chrome/Chromium and build tools
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONPATH=/app

# Copy requirements first for better caching
COPY webapp/requirements.txt /app/requirements.txt

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY webapp/ /app/

# Create necessary directories
RUN mkdir -p /app/logs
RUN mkdir -p /app/data
RUN mkdir -p /app/data/results

# Set proper permissions
RUN chmod -R 755 /app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Expose port
EXPOSE 8080

# Set environment variable for port
ENV PORT=8080

# Run the application
CMD ["gunicorn", "app:app", "--workers", "2", "--threads", "2", "--timeout", "60", "--bind", "0.0.0.0:8080", "--access-logfile", "-", "--error-logfile", "-"]
