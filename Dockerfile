FROM python:3.11.5-slim-bullseye AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Create non-root user
RUN useradd -m -u 1000 supportbotuser

# Set up working directory
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir uv==0.2.15 \
    && uv pip install --no-cache-dir -r requirements.txt --system \
    && uv pip freeze --system

# Copy application code
COPY --chown=supportbotuser:supportbotuser . .

# Create necessary directories and set permissions
RUN mkdir -p logs \
    && chown -R supportbotuser:supportbotuser /app

# Switch to non-root user
USER supportbotuser

# Run the bot
CMD ["python", "main.py"] 
