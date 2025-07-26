# API Refactoring - File Upload and S3 Integration

## Overview
Complete refactoring of the ADDIT API from base64 image handling to file upload with S3 storage integration.

## Key Changes
- **Input Method**: Changed from base64 encoded images to file path input (`/tmp/` directory)
- **Output Method**: Dual system - S3 upload when configured, temporary download URLs as fallback
- **LLM Integration**: Auto-generates both `subject_token` and `prompt_source` from uploaded images
- **API Simplification**: Reduced required fields to just `source_image` path and `prompt_target`

## New API Structure
```json
{
  "input": {
    "source_image": "/tmp/uploaded_image.jpg",
    "prompt_target": "a red car in the driveway",
    "seed_src": 6311  // optional
  }
}
```

## Response Format
```json
{
  "image_url": "https://s3.../image.jpg",  // or "/download/job_id.jpg"
  "metadata": {
    "prompt_source": "A photo of a house with a driveway",  // auto-generated
    "prompt_target": "a red car in the driveway",
    "subject_token": "car",  // auto-generated 1-2 words
    "seed_src": 6311
  },
  "job_id": "uuid"
}
```

## S3 Integration
Environment variables for S3 configuration:
- `S3_BUCKET_ID` - S3 bucket name
- `S3_SECRET_KEY` - S3 secret access key
- `S3_URL` - S3 endpoint URL
- `S3_ZONE` - S3 region/zone

## Technical Benefits
- **Performance**: File handling instead of base64 reduces payload size
- **Storage Flexibility**: Optional S3 with temp file fallback
- **User Experience**: Simplified API with auto-generated prompts
- **Resource Management**: Automatic cleanup of temporary files
- **Error Handling**: Comprehensive fallback mechanisms