FROM python:3.12-slim

LABEL org.opencontainers.image.title="CIEL API"
LABEL org.opencontainers.image.description="CIEL — Conscience Intégrale d'Évolution Limitrophe"
LABEL org.opencontainers.image.version="v∞.8"
LABEL org.opencontainers.image.licenses="AGPL-3.0-or-later"

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY pyproject.toml README.md ./
COPY ciel/ ciel/
RUN pip install --no-cache-dir -e ".[dev]"

# Expose API port
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8765/v1/health').raise_for_status()"

# Run CIEL API server
ENTRYPOINT ["ciel-api"]
CMD ["--host", "0.0.0.0", "--port", "8765"]
