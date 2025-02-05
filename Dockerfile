# Use official Python image
FROM python:3.10

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot files into the container
COPY . .

# Expose Flask port (Heroku uses this)
EXPOSE 8080

# Run the bot
CMD ["python", "spytera.py"]
