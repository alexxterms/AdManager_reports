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

# Start the combined OAuth + Socket Mode service (Railway: expose a web domain on this service)
CMD ["python", "-m", "src.combined_service"]
