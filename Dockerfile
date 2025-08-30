# Use official Python 3.11 slim image as base
FROM python:3.11-slim

# Set the working directory to /app
WORKDIR /app

# Copy requirements.txt first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into /app
COPY . .

# Install the package in editable mode
RUN pip install -e .

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash organizer && \
    chown -R organizer:organizer /app

# Switch to non-root user
USER organizer

# Set the entrypoint to use the organizer CLI
ENTRYPOINT ["organizer"]

# Default command (can be overridden)
CMD ["--help"]

# Add labels for better maintainability
LABEL maintainer="Ruhe Tarannum <ruhetarannum@gmail.com>"
LABEL version="0.1.0"
LABEL description="Automated File Organizer - A Python tool to organize files into categorized folders"
LABEL repository="https://github.com/Ruhetarannum/automated-file-organizer"
