# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY live_interview_service/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the microservice code
COPY live_interview_service/ ./live_interview_service/

# Copy eye_monitor directory for proctoring
# Note: Build from parent directory (Gemini_Engine) to access eye_monitor
# Example: docker build -f live_interview_service/Dockerfile -t live-interview-service .
# If eye_monitor doesn't exist, this will fail - that's OK, proctoring will be disabled
COPY eye_monitor/ ./eye_monitor/

# Create directory for output files
RUN mkdir -p /app/outputs

# Expose the service port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health')" || exit 1

# Set PYTHONPATH to include parent directory
ENV PYTHONPATH=/app

# Run the service
CMD ["uvicorn", "live_interview_service.service:app", "--host", "0.0.0.0", "--port", "8001"]
