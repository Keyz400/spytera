# Use Ubuntu as the base image (Heroku uses Debian by default)
FROM ubuntu:20.04

# Set non-interactive mode to prevent installation issues
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt update && apt install -y wget curl unzip software-properties-common \
    && apt install -y nodejs npm python3 python3-pip git \
    && apt clean

# Install Playwright and required browsers
RUN pip3 install --no-cache-dir playwright pyrogram requests bs4 pymongo aiohttp \
    && playwright install \
    && playwright install-deps

# Set working directory
WORKDIR /app

# Copy bot files
COPY . .

# Expose port (Heroku dynamically assigns a port)
ENV PORT=8080
EXPOSE 8080

# Run bot script
CMD ["python", "spytera.py"]
