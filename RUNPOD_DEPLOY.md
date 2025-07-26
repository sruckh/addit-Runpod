# RunPod Serverless Deployment Guide for ADDIT

This guide explains how to deploy the ADDIT (Add Object to Image) project as a RunPod serverless function.

## 📋 Overview

The ADDIT project has been converted to a RunPod serverless function with the following features:
- **GPU-accelerated** inference using CUDA
- **Model caching** for improved performance
- **File upload support** with temporary file handling
- **S3 integration** for cloud storage with fallback to temporary URLs
- **Auto-generated prompts** using Qwen2.5-VL-72B for intelligent image analysis
- **Comprehensive error handling** and logging
- **Simplified API** requiring only image file and target prompt

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

### New Simplified API Design

The API has been completely refactored for better usability:
- **File uploads** instead of base64 encoding
- **Auto-generated prompts** from image analysis
- **S3 storage** with temporary URL fallback
- **Single endpoint** with minimal required fields

### Request Format

```json
POST /run
{
  "input": {
    "source_image": "/tmp/uploaded_image.jpg",
    "prompt_target": "a red car in the driveway",
    "seed_src": 6311
  }
}
```

**Required Fields:**
- `source_image`: File path to uploaded image (stored in `/tmp/`)
- `prompt_target`: What you want to add to the image

**Optional Fields:**
- `seed_src`: Random seed for reproducible results (default: 6311)
- `seed_obj`: Object insertion seed (default: 1)
- `extended_scale`: Scale factor (default: 1.1)
- `structure_transfer_step`: Transfer step (default: 4)
- `blend_steps`: Blending steps array (default: [18])
- `localization_model`: Model type (default: "attention")
- `use_offset`: Use offset (default: false)
- `use_inversion`: Use inversion (default: true)

### Response Format
```json
{
  "image_url": "https://s3.amazonaws.com/bucket/job_id_edited.jpg",
  "metadata": {
    "prompt_source": "A photo of a house with a driveway",
    "prompt_target": "a red car in the driveway", 
    "subject_token": "car",
    "seed_src": 6311,
    "seed_obj": 1,
    "extended_scale": 1.1,
    "structure_transfer_step": 4,
    "blend_steps": [18],
    "localization_model": "attention",
    "use_offset": false,
    "use_inversion": true
  },
  "job_id": "uuid-string"
}
```

**Response Fields:**
- `image_url`: S3 URL or temporary download URL (`/download/job_id.jpg`)
- `metadata`: All processing parameters including auto-generated prompts
- `job_id`: Unique identifier for this processing job

### Auto-Generated Fields

The API automatically generates these fields using Qwen2.5-VL-72B:
- `prompt_source`: Single sentence describing the source image
- `subject_token`: 1-2 word description of the main subject being added

## ⚙️ Configuration

### Environment Variables

**Required:**
- `HF_TOKEN`: Hugging Face authentication token (required for FLUX.1-dev model access)

**Optional:**
- `HF_HOME`: Hugging Face cache directory (default: `/app/.cache/huggingface`)
- `PYTHONUNBUFFERED`: Enable unbuffered logging (default: `1`)
- `OPENROUTER_API_KEY`: OpenRouter API key for auto-prompt generation (optional, fallback to simple prompts if not provided)

**S3 Storage (All Required for S3 to Activate):**
- `S3_BUCKET_ID`: S3 bucket name/identifier
- `S3_SECRET_KEY`: S3 secret access key
- `S3_URL`: S3 endpoint URL (AWS or compatible service)
- `S3_ZONE`: S3 region/zone identifier

**Note:** If S3 variables are not configured, the API automatically falls back to temporary file serving with download URLs.

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

3. **File Upload Issues**
   - Ensure image file is properly uploaded to `/tmp/` directory
   - Check image format (PNG/JPEG supported)
   - Verify file permissions and accessibility

### Auto-Prompt Generation

The API automatically generates intelligent prompts using Qwen2.5-VL-72B:

**Benefits:**
- **Simplified API**: Just provide `prompt_target` (what to add)
- **Intelligent Analysis**: AI analyzes your source image to create contextual descriptions
- **Better Results**: Prompts are tailored to the specific scene and lighting
- **No Manual Crafting**: Eliminates need to write detailed prompt descriptions

**How it works:**
1. Upload your image file to the API
2. Specify what you want to add in `prompt_target`
3. Qwen2.5-VL-72B analyzes the image and generates:
   - `prompt_source`: Detailed description of the current scene
   - `subject_token`: 1-2 word identifier of the main subject

**Example:**
```json
{
  "input": {
    "source_image": "/tmp/bedroom_photo.jpg",
    "prompt_target": "a cat lying on the bed"
  }
}
```

**Auto-generated prompts might be:**
- `prompt_source`: "A cozy bedroom with warm lighting and a neatly made bed"
- `subject_token`: "cat"

### S3 Storage Integration

The API supports optional S3 storage for processed images:

**Benefits:**
- **Cloud Storage**: Permanent storage of processed images
- **CDN Support**: Fast global image delivery
- **Automatic Fallback**: Uses temporary URLs if S3 not configured

**Configuration:**
Set all four S3 environment variables to enable:
- `S3_BUCKET_ID`, `S3_SECRET_KEY`, `S3_URL`, `S3_ZONE`

**Response Options:**
- **With S3**: Returns permanent S3 URL (`https://s3.../image.jpg`)
- **Without S3**: Returns temporary download URL (`/download/job_id.jpg`)

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
- [ ] Environment variables configured:
  - [ ] `HF_TOKEN` set in RunPod dashboard (required)
  - [ ] `OPENROUTER_API_KEY` set in RunPod dashboard (optional, for auto-prompts)
  - [ ] S3 variables configured if using cloud storage (optional):
    - [ ] `S3_BUCKET_ID`
    - [ ] `S3_SECRET_KEY`
    - [ ] `S3_URL`
    - [ ] `S3_ZONE`
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