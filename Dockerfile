# ---- Base image: small official Python image ----
FROM python:3.12-slim

# Don't write .pyc files, and print logs immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ACEEST_DB=/app/data/aceest_fitness.db

WORKDIR /app

# Security: create a non-root user and give it the app folder
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

# Install dependencies first (this layer is cached until requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and tests, owned by the non-root user
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 5000

# Docker checks the /health endpoint every 30s
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Production web server (not Flask's debug server)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
