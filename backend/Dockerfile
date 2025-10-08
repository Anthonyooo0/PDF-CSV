FROM python:3.12-slim

# Install system dependencies for PDF processing
RUN apt-get update && \
    apt-get install -y tesseract-ocr poppler-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install Python dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi --no-root

# Copy application code
COPY app ./app

# Expose port
EXPOSE 8000

# Run the application
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
