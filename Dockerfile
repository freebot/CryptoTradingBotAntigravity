FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for some ML libraries)
# RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Run the bot
CMD ["python", "main.py"]
