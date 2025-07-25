# Use official PyTorch base image with CUDA 12.6 and PyTorch 2.6 - specify amd64 for RunPod
FROM --platform=linux/amd64 pytorch/pytorch:2.6.0-cuda12.6-cudnn9-devel

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
RUN python -c "import torch; \
    from diffusers import FluxPipeline; \
    import logging; \
    logging.basicConfig(level=logging.INFO); \
    print('🔄 Pre-loading FLUX.1-dev models...'); \
    try: \
        pipe = FluxPipeline.from_pretrained('black-forest-labs/FLUX.1-dev', torch_dtype=torch.bfloat16, cache_dir='/app/.cache/huggingface'); \
        print('✅ FLUX.1-dev pipeline loaded successfully'); \
        pipe.to('cuda' if torch.cuda.is_available() else 'cpu'); \
        print('✅ Models moved to device and cached'); \
        del pipe; \
        torch.cuda.empty_cache(); \
        print('✅ Model pre-loading complete - ready for serverless deployment'); \
    except Exception as e: \
        print(f'⚠️ Model pre-loading failed: {e}'); \
        print('⚠️ Will fallback to lazy loading on first request')"

# Expose port (for local testing)
EXPOSE 8000

# Start the handler
CMD ["python", "-u", "handler.py"]