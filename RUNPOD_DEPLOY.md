# RunPod Serverless Deployment Guide for ADDIT

This guide explains how to deploy the ADDIT (Add Object to Image) project as a RunPod serverless function.

## 📋 Overview

The ADDIT project has been converted to a RunPod serverless function with the following features:
- **GPU-accelerated** inference using CUDA
- **Model caching** for improved performance
- **Base64 image handling** for API compatibility
- **Comprehensive error handling** and logging
- **Configurable parameters** for flexible usage

## 🚀 Quick Start

### 1. Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Test locally
python test_local.py
```

### 2. Deploy to RunPod

#### Option A: Using RunPod CLI
```bash
# Install RunPod CLI
npm install -g runpodctl

# Deploy
runpodctl deploy runpod.toml
```

#### Option B: Using Docker Build
```bash
# Build Docker image
docker build -t addit-serverless .

# Test locally
docker run -p 8000:8000 addit-serverless
```

## 📡 API Usage

### Request Format
```json
POST /run
{
  "input": {
    "source_image": "<base64-encoded-image>",
    "prompt_source": "A photo of a bed in a dark room",
    "prompt_target": "A photo of a cat lying on a bed in a dark room",
    "subject_token": "cat",
    "seed_src": 6311,
    "seed_obj": 1,
    "extended_scale": 1.1,
    "structure_transfer_step": 4,
    "blend_steps": [18],
    "localization_model": "attention",
    "use_offset": false,
    "use_inversion": true
  }
}
```

### Response Format
```json
{
  "output": {
    "source_image": "<base64-encoded-source>",
    "edited_image": "<base64-encoded-edited>",
    "metadata": {
      "prompt_source": "...",
      "prompt_target": "...",
      "subject_token": "...",
      "seed_src": 6311,
      "seed_obj": 1,
      "extended_scale": 1.1,
      "structure_transfer_step": 4,
      "blend_steps": [18],
      "localization_model": "attention",
      "use_offset": false,
      "use_inversion": true
    }
  }
}
```

## ⚙️ Configuration

### Environment Variables
- `HF_HOME`: Hugging Face cache directory (default: `/app/.cache/huggingface`)
- `PYTHONUNBUFFERED`: Enable unbuffered logging (default: `1`)

### RunPod Configuration (`runpod.toml`)
- **GPU**: 1x GPU (required for FLUX.1-dev)
- **Memory**: 16GB RAM
- **CPU**: 4 cores
- **Timeout**: 300 seconds
- **Max Concurrency**: 1 (to manage GPU memory)

## 📊 Performance Notes

- **Cold Start**: ~30-60 seconds (model loading)
- **Warm Start**: ~5-10 seconds (cached models)
- **Memory Usage**: ~8-12GB GPU memory
- **Processing Time**: ~10-30 seconds per image

## 🔧 Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   - Reduce batch size or image resolution
   - Ensure GPU has sufficient memory (16GB+ recommended)

2. **Model Loading Timeout**
   - Increase timeout in `runpod.toml`
   - Check network connectivity for model downloads

3. **Image Encoding Issues**
   - Ensure base64 encoding is correct
   - Check image format (PNG/JPEG supported)

### Debug Mode
```bash
# Enable debug logging
export PYTHONUNBUFFERED=1
python handler.py
```

## 📝 Deployment Checklist

- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Docker image builds successfully (`docker build -t addit-serverless .`)
- [ ] Local testing passes (`python test_local.py`)
- [ ] RunPod configuration validated (`runpod.toml`)
- [ ] Environment variables configured
- [ ] GPU quota available on RunPod account

## 🔄 Updates

To update the serverless function:
1. Modify code as needed
2. Update version in `requirements.txt` if needed
3. Rebuild Docker image
4. Redeploy to RunPod

## 📞 Support

For issues or questions:
- Check the logs in RunPod dashboard
- Verify input format matches API specification
- Ensure sufficient GPU memory allocation