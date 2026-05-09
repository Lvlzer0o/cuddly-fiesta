# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for Tkinter and matplotlib
RUN apt-get update && apt-get install -y \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install the package in development mode
RUN pip install -e .

# Set the default command to run the GUI application
CMD ["python", "-m", "cuddly_fiesta", "gui"]

# Expose any necessary ports (if your application uses network ports)
# EXPOSE 8000

# Set environment variables if needed
# ENV PYTHONUNBUFFERED=1

# Add a volume for persistent data (if needed)
# VOLUME /app/data

# Set up a non-root user (recommended for security)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Set environment variables for matplotlib to use a non-interactive backend
ENV MPLBACKEND=agg
