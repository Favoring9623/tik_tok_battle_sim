FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_DEBUG=false

# Run the web server
CMD ["python", "-c", "from web.backend.app import run_server; run_server(host='0.0.0.0', port=5000)"]
