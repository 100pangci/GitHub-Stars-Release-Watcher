FROM python:3.12-slim

LABEL org.opencontainers.image.title="GitHub Stars Release Watcher"
LABEL org.opencontainers.image.description="Monitor your GitHub starred repositories for new releases"
LABEL org.opencontainers.image.version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Create app user and directories
RUN groupadd -r app && \
    useradd -r -g app -d /app -s /sbin/nologin app && \
    mkdir -p /app /data && \
    chown -R app:app /app /data

# Set working directory
WORKDIR /app

# Install system build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libc6-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY app/ app/
COPY tests/ tests/

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    jinja2 \
    sqlalchemy \
    aiosqlite \
    httpx \
    apscheduler \
    pydantic \
    pydantic-settings \
    passlib[bcrypt] \
    python-multipart \
    itsdangerous && \
    rm -rf /root/.cache/pip

# Remove build dependencies
RUN apt-get purge -y --auto-remove gcc libc6-dev && \
    rm -rf /var/lib/apt/lists/*

# Ensure /data is writeable and fix permissions
RUN chown -R app:app /app /data

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]