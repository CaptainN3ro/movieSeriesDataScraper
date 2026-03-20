FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 2000

CMD ["gunicorn", "--bind", "0.0.0.0:2000", "--workers", "2", "--timeout", "30", "app:app"]
