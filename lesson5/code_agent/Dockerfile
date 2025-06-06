# Dockerfile for sandboxed Python environment
FROM python:3.10-slim

# Copy requirements.txt into the image
COPY requirements.txt /app/requirements.txt

# Install required Python libraries for data analysis and plotting
RUN pip install --no-cache-dir -r /app/requirements.txt

# Add a non-root user and home directory
RUN useradd -m sandboxuser
USER sandboxuser

WORKDIR /app

# The container will run as this non-root user by default (for security).
# No explicit CMD is needed; the Runner will specify the command to run.
