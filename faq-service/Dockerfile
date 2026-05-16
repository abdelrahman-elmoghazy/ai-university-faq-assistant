FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create secure upload directory (outside public folder)
RUN mkdir -p /app/secure_uploads && chmod 700 /app/secure_uploads

# Environment variables
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5001
ENV PYTHONPATH=/app

EXPOSE 5001

CMD ["python", "main.py"]
