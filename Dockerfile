# Use an official Python runtime as a parent image.
FROM python:3.9-slim

# Set the working directory to /app.
WORKDIR /app

# Copy requirements.txt and install Python dependencies.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Expose the port that Cloud Run sets via the $PORT environment variable.
EXPOSE 8080

# Run the Dash app using Gunicorn.
# Cloud Run will set the PORT environment variable. Gunicorn will bind to it.
CMD exec gunicorn app:server --bind 0.0.0.0:$PORT --workers 1 --threads 8
