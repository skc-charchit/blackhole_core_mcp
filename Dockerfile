FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for building pandas and other packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip to avoid known pip issues
RUN pip install --upgrade pip

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code into the container
COPY . .

# Expose port (optional)
EXPOSE 8000

# Run your app via Uvicorn
CMD ["uvicorn", "data.api.mcp_adapter:app", "--host", "0.0.0.0", "--port", "8000"]
