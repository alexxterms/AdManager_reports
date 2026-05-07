FROM mcr.microsoft.com/playwright/python:latest

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Ensure Playwright browsers and dependencies are installed (image usually includes them)
RUN playwright install --with-deps || true

ENV PYTHONUNBUFFERED=1

# Start as a worker process (Railway: choose "Worker")
CMD ["python", "-m", "src.app"]
