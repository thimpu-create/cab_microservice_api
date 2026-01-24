# -------------------------------
# Base Image
# -------------------------------
FROM python:3.11-slim

# -------------------------------
# Set work directory
# -------------------------------
WORKDIR /app

# -------------------------------
# Install system dependencies
# -------------------------------
RUN apt-get update && apt-get install -y \
    libpq-dev gcc build-essential postgresql-client curl \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------
# Copy requirements
# -------------------------------
COPY requirements.txt .

# -------------------------------
# Install Python packages
# -------------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------
# Copy application code
# -------------------------------
COPY . .

# -------------------------------
# Expose default port
# -------------------------------
EXPOSE 8000

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
