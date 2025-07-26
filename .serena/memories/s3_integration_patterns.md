# S3 Integration Patterns

## Implementation Overview
The ADDIT API supports optional S3 integration for storing processed images with automatic fallback to temporary file serving.

## S3 Configuration
Required environment variables (all must be present for S3 to activate):
- `S3_BUCKET_ID` - The S3 bucket identifier/name
- `S3_SECRET_KEY` - S3 secret access key for authentication
- `S3_URL` - S3 endpoint URL (can be AWS or compatible service)
- `S3_ZONE` - S3 region/zone identifier

## Fallback Strategy
1. **S3 Available**: Upload image to S3 and return public S3 URL
2. **S3 Not Configured**: Save to `/tmp/` and return temporary download URL format `/download/{job_id}.jpg`
3. **S3 Upload Fails**: Automatically fall back to temporary file serving

## Key Functions
- `upload_to_s3(image, filename)` - Handles S3 upload with error handling
- `create_temp_url(image, job_id)` - Creates temporary download alternative
- `cleanup_temp_files(job_id)` - Cleans up temporary files after processing

## Error Handling
- Graceful degradation when boto3 not available
- Automatic fallback on S3 connection failures
- Comprehensive logging for troubleshooting
- No user-facing errors for S3 issues (transparent fallback)

## Usage Pattern
```python
# Try S3 first
image_url = upload_to_s3(edited_image, f"{job_id}_edited.jpg")

if not image_url:
    # Fallback to temporary URL
    image_url = create_temp_url(edited_image, f"{job_id}_edited")
```

## Security Considerations
- S3 credentials stored as environment variables only
- No hardcoded credentials in code
- Proper error handling prevents credential leakage