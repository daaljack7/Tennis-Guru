FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose port
EXPOSE 8080

# Run the app with logging enabled
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--access-logfile", "-", "--error-logfile", "-", "--capture-output", "--timeout", "120", "app:app"]
