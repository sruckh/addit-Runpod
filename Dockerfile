# Use official PyTorch base image with CUDA 12.6 and PyTorch 2.6 for RunPod
FROM pytorch/pytorch:2.6.0-cuda12.6-cudnn9-devel

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HF_HOME=/app/.cache/huggingface

# Create cache directory
RUN mkdir -p /app/.cache/huggingface

# Pre-load models during build to eliminate cold start delays
RUN python preload_models.py

# Expose port (for local testing)
EXPOSE 8000

# Start the handler
CMD ["python", "-u", "handler.py"]