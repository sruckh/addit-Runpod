#!/usr/bin/env python3
"""
RunPod Serverless Handler for ADDIT (Add Object to Image)
This handler provides a serverless API for adding objects to images using ADDIT.
"""

import os
import json
import base64
import torch
from PIL import Image
import io
import logging
import requests
import uuid
import tempfile
import shutil
from typing import Dict, Any, Tuple, Optional
try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

from addit_flux_pipeline import AdditFluxPipeline
from addit_flux_transformer import AdditFluxTransformer2DModel
from addit_scheduler import AdditFlowMatchEulerDiscreteScheduler
from addit_methods import add_object_real

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for model caching
pipe = None
device = None
model_loaded = False

def generate_prompt_with_qwen(image_base64: str, prompt_target: str) -> Tuple[str, str]:
    """
    Generate prompt_source and subject_token using Qwen2.5-VL-72B (free) via OpenRouter.
    
    Args:
        image_base64: Base64 encoded source image
        prompt_target: User's input describing what to add to the image
    
    Returns:
        Tuple of (prompt_source, subject_token)
    """
    try:
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if not openrouter_key:
            logger.warning("OPENROUTER_API_KEY not found, using fallback prompts")
            # Extract potential subject from prompt_target for fallback
            words = prompt_target.lower().split()
            subject_token = words[0] if words else "object"
            return f"A photo showing the current scene", subject_token
        
        # Prepare the API request
        headers = {
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Analyze this image and provide two things:

1. A single sentence description of what you see in the image (this will be the prompt_source)
2. A 1-2 word description of the main subject that the user wants to add: "{prompt_target}"

Respond with ONLY this format:
PROMPT_SOURCE: [single sentence describing the current image]  
SUBJECT_TOKEN: [1-2 words describing the main subject from the user's prompt_target]

For example, if the user wants to add "a red car in the driveway", the subject_token should be "car" or "red car"."""

        payload = {
            "model": "qwen/qwen2.5-vl-72b-instruct:free",
            "messages": [
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            "max_tokens": 200,
            "temperature": 0.3
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse the response
            lines = content.strip().split('\n')
            prompt_source = ""
            subject_token = ""
            
            for line in lines:
                if line.startswith("PROMPT_SOURCE:"):
                    prompt_source = line.replace("PROMPT_SOURCE:", "").strip()
                elif line.startswith("SUBJECT_TOKEN:"):
                    subject_token = line.replace("SUBJECT_TOKEN:", "").strip()
            
            # Fallback if parsing failed
            if not prompt_source:
                prompt_source = "A photo showing the current scene"
            if not subject_token:
                # Extract potential subject from prompt_target as fallback
                words = prompt_target.lower().split()
                subject_token = words[0] if words else "object"
            
            logger.info(f"Generated prompt_source: {prompt_source}")
            logger.info(f"Generated subject_token: {subject_token}")
            
            return prompt_source, subject_token
        else:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            # Fallback
            words = prompt_target.lower().split()
            subject_token = words[0] if words else "object"
            return "A photo showing the current scene", subject_token
            
    except Exception as e:
        logger.error(f"Error generating prompt with Qwen: {str(e)}")
        # Fallback
        words = prompt_target.lower().split()
        subject_token = words[0] if words else "object"
        return "A photo showing the current scene", subject_token

def load_models():
    """Load and cache the ADDIT models."""
    global pipe, device, model_loaded
    
    if model_loaded:
        logger.info("Models already loaded, using cached version")
        return
    
    try:
        logger.info("Loading ADDIT models...")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {device}")
        
        # Get HF token for authentication
        hf_token = os.getenv('HF_TOKEN')
        if hf_token:
            logger.info("Using HF_TOKEN for model authentication")
        
        # Load transformer - use cached models if available
        my_transformer = AdditFluxTransformer2DModel.from_pretrained(
            "black-forest-labs/FLUX.1-dev",
            subfolder="transformer",
            torch_dtype=torch.bfloat16,
            cache_dir=os.getenv('HF_HOME', '/app/.cache/huggingface'),
            token=hf_token
        )
        
        # Load pipeline - use cached models if available
        pipe = AdditFluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-dev",
            transformer=my_transformer,
            torch_dtype=torch.bfloat16,
            cache_dir=os.getenv('HF_HOME', '/app/.cache/huggingface'),
            token=hf_token
        ).to(device)
        
        # Configure scheduler
        pipe.scheduler = AdditFlowMatchEulerDiscreteScheduler.from_config(pipe.scheduler.config)
        
        model_loaded = True
        logger.info("Models loaded successfully from cache")
        
    except Exception as e:
        logger.error(f"Error loading models: {str(e)}")
        raise

def decode_image(image_data: str) -> Image.Image:
    """Decode base64 image string to PIL Image."""
    try:
        image_bytes = base64.b64decode(image_data)
        return Image.open(io.BytesIO(image_bytes)).convert('RGB').resize((1024, 1024))
    except Exception as e:
        raise ValueError(f"Invalid image data: {str(e)}")

def encode_image(image: Image.Image) -> str:
    """Encode PIL Image to base64 string."""
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def save_image_to_temp(image: Image.Image, job_id: str) -> str:
    """Save PIL Image to temporary file and return the path."""
    temp_path = f"/tmp/{job_id}.jpg"
    image.save(temp_path, format='JPEG', quality=95)
    return temp_path

def load_image_from_file(file_path: str) -> Image.Image:
    """Load image from file path and convert to RGB."""
    try:
        image = Image.open(file_path).convert('RGB').resize((1024, 1024))
        return image
    except Exception as e:
        raise ValueError(f"Invalid image file: {str(e)}")

def upload_to_s3(image: Image.Image, filename: str) -> Optional[str]:
    """Upload image to S3 if configured, return S3 URL or None."""
    if not S3_AVAILABLE:
        logger.warning("boto3 not available, cannot upload to S3")
        return None
    
    # Check for S3 configuration
    s3_bucket = os.getenv('S3_BUCKET_ID')
    s3_secret = os.getenv('S3_SECRET_KEY')
    s3_url = os.getenv('S3_URL')
    s3_zone = os.getenv('S3_ZONE')
    
    if not all([s3_bucket, s3_secret, s3_url, s3_zone]):
        logger.info("S3 not fully configured, skipping upload")
        return None
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=s3_bucket,
            aws_secret_access_key=s3_secret,
            endpoint_url=s3_url,
            region_name=s3_zone
        )
        
        # Convert image to bytes
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=95)
        buffer.seek(0)
        
        # Upload to S3
        s3_client.upload_fileobj(
            buffer,
            s3_bucket,
            filename,
            ExtraArgs={'ContentType': 'image/jpeg'}
        )
        
        # Return S3 URL
        s3_image_url = f"{s3_url}/{s3_bucket}/{filename}"
        logger.info(f"Image uploaded to S3: {s3_image_url}")
        return s3_image_url
        
    except ClientError as e:
        logger.error(f"S3 upload failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        return None

def create_temp_url(image: Image.Image, job_id: str) -> str:
    """Create temporary file and return download path."""
    temp_path = save_image_to_temp(image, job_id)
    # In a real server, this would be a proper URL to download the temp file
    # For now, return the file path
    return f"/download/{job_id}.jpg"

def cleanup_temp_files(job_id: str):
    """Clean up temporary files for a job."""
    temp_files = [
        f"/tmp/{job_id}.jpg",
        f"/tmp/{job_id}_input.jpg",
        f"/tmp/{job_id}_output.jpg"
    ]
    
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                logger.debug(f"Cleaned up temp file: {temp_file}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {temp_file}: {str(e)}")

def validate_input(job_input: Dict[str, Any]) -> None:
    """Validate the input parameters for the new API structure."""
    # Source image file path is always required
    if 'source_image' not in job_input:
        raise ValueError("Missing required field: source_image (file path)")
    
    # Prompt target (what user wants to add) is always required
    if 'prompt_target' not in job_input:
        raise ValueError("Missing required field: prompt_target (what to add to the image)")
    
    # Validate that source_image is a valid file path
    source_image_path = job_input['source_image']
    if not isinstance(source_image_path, str) or not source_image_path.strip():
        raise ValueError("source_image must be a valid file path string")
    
    # Validate that prompt_target is not empty
    prompt_target = job_input['prompt_target']
    if not isinstance(prompt_target, str) or not prompt_target.strip():
        raise ValueError("prompt_target must be a non-empty string")
    
    # Validate optional seed_src is an integer if provided
    if 'seed_src' in job_input:
        seed_src = job_input['seed_src']
        if not isinstance(seed_src, int) or seed_src < 0:
            raise ValueError("seed_src must be a non-negative integer")

def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main handler function for RunPod serverless.
    
    Expected input format:
    {
        "source_image": "/tmp/uploaded_image.jpg",
        "prompt_target": "a red car in the driveway",
        "seed_src": 6311  # optional
    }
    
    Returns:
    {
        "image_url": "https://s3.../image.jpg" | "/download/job_id.jpg",
        "metadata": {
            "prompt_source": "A photo of a house with a driveway",
            "prompt_target": "a red car in the driveway", 
            "subject_token": "car",
            "seed_src": 6311
        }
    }
    """
    
    job_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Starting ADDIT processing for job {job_id}...")
        
        # Load models (cached after first load)
        load_models()
        
        # Parse input
        job_input = job.get('input', {})
        validate_input(job_input)
        
        # Load source image from file
        source_image_path = job_input['source_image']
        source_image = load_image_from_file(source_image_path)
        logger.info(f"Source image loaded from: {source_image_path}")
        
        # Get user's prompt target
        prompt_target = job_input['prompt_target']
        
        # Convert image to base64 for LLM processing
        source_b64 = encode_image(source_image)
        
        # Auto-generate prompt_source and subject_token using LLM
        logger.info(f"Auto-generating prompts for target: {prompt_target}")
        prompt_source, subject_token = generate_prompt_with_qwen(source_b64, prompt_target)
        
        # Get optional parameters
        seed_src = job_input.get('seed_src', 6311)
        seed_obj = job_input.get('seed_obj', 1)
        extended_scale = job_input.get('extended_scale', 1.1)
        structure_transfer_step = job_input.get('structure_transfer_step', 4)
        blend_steps = job_input.get('blend_steps', [18])
        localization_model = job_input.get('localization_model', 'attention')
        use_offset = job_input.get('use_offset', False)
        use_inversion = job_input.get('use_inversion', True)
        
        # Process with ADDIT
        logger.info(f"Processing with seeds: src={seed_src}, obj={seed_obj}")
        
        src_image, edited_image = add_object_real(
            pipe=pipe,
            source_image=source_image,
            prompt_source=prompt_source,
            prompt_object=prompt_target,
            subject_token=subject_token,
            seed_src=seed_src,
            seed_obj=seed_obj,
            extended_scale=extended_scale,
            structure_transfer_step=structure_transfer_step,
            blend_steps=blend_steps,
            localization_model=localization_model,
            use_offset=use_offset,
            show_attention=False,
            use_inversion=use_inversion,
            display_output=False
        )
        
        # Handle output - try S3 first, fallback to temp URL
        image_filename = f"{job_id}_edited.jpg"
        image_url = upload_to_s3(edited_image, image_filename)
        
        if not image_url:
            # S3 not configured or failed, create temp URL
            image_url = create_temp_url(edited_image, f"{job_id}_edited")
            logger.info(f"Created temporary download URL: {image_url}")
        
        # Prepare metadata
        metadata = {
            "prompt_source": prompt_source,
            "prompt_target": prompt_target,
            "subject_token": subject_token,
            "seed_src": seed_src,
            "seed_obj": seed_obj,
            "extended_scale": extended_scale,
            "structure_transfer_step": structure_transfer_step,
            "blend_steps": blend_steps,
            "localization_model": localization_model,
            "use_offset": use_offset,
            "use_inversion": use_inversion
        }
        
        # Clean up input temp file if it exists
        try:
            if os.path.exists(source_image_path) and source_image_path.startswith('/tmp/'):
                os.remove(source_image_path)
                logger.debug(f"Cleaned up input file: {source_image_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup input file: {str(e)}")
        
        logger.info(f"ADDIT processing completed successfully for job {job_id}")
        
        return {
            "image_url": image_url,
            "metadata": metadata,
            "job_id": job_id
        }
        
    except Exception as e:
        logger.error(f"Error in handler for job {job_id}: {str(e)}")
        
        # Clean up on failure
        cleanup_temp_files(job_id)
        
        return {
            "error": str(e),
            "status": "failed",
            "job_id": job_id
        }

# For local testing
if __name__ == "__main__":
    # Test the handler locally
    import sys
    
    # Create a simple test
    test_input = {
        "source_image": "/tmp/test_image.jpg",  # Path to test image file
        "prompt_target": "a dog lying on the bed",
        "seed_src": 6311
    }
    
    result = handler({"input": test_input})
    print(json.dumps(result, indent=2))