FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for some ML libraries)
# RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .
# Install Nginx
RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and config
COPY . .
COPY nginx.conf /etc/nginx/nginx.conf

# Expose the single port supported by Hugging Face Spaces
EXPOSE 7860

# Run the hybrid startup script
CMD ["./start.sh"]
