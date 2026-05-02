# Use the official lightweight Python image
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the Cloud Run logs
ENV PYTHONUNBUFFERED True

# Set the working directory
ENV APP_HOME /app
WORKDIR $APP_HOME

# Copy local code to the container image
COPY . ./

# Install production dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Ensure gunicorn is installed for production serving
RUN pip install --no-cache-dir gunicorn

# Run the web service on container startup using Gunicorn
# Cloud Run injects the $PORT environment variable automatically (default 8080)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 wsgi:application
