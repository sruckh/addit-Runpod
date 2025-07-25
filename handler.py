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
from typing import Dict, Any, Tuple

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
        
        # Load transformer - use cached models if available
        my_transformer = AdditFluxTransformer2DModel.from_pretrained(
            "black-forest-labs/FLUX.1-dev",
            subfolder="transformer",
            torch_dtype=torch.bfloat16,
            cache_dir=os.getenv('HF_HOME', '/app/.cache/huggingface')
        )
        
        # Load pipeline - use cached models if available
        pipe = AdditFluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-dev",
            transformer=my_transformer,
            torch_dtype=torch.bfloat16,
            cache_dir=os.getenv('HF_HOME', '/app/.cache/huggingface')
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

def validate_input(job_input: Dict[str, Any]) -> None:
    """Validate the input parameters."""
    required_fields = ['source_image', 'prompt_source', 'prompt_target', 'subject_token']
    
    for field in required_fields:
        if field not in job_input:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate subject token appears in target prompt
    subject_token = job_input['subject_token']
    prompt_target = job_input['prompt_target']
    
    if subject_token not in prompt_target:
        raise ValueError(f"Subject token '{subject_token}' must appear in prompt_target")

def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main handler function for RunPod serverless.
    
    Expected input format:
    {
        "source_image": "<base64 encoded image>",
        "prompt_source": "A photo of a bed in a dark room",
        "prompt_target": "A photo of a dog lying on a bed in a dark room",
        "subject_token": "dog",
        "seed_src": 6311,
        "seed_obj": 1,
        "extended_scale": 1.1,
        "structure_transfer_step": 4,
        "blend_steps": [18],
        "localization_model": "attention",
        "use_offset": false,
        "use_inversion": true
    }
    
    Returns:
    {
        "source_image": "<base64 encoded source image>",
        "edited_image": "<base64 encoded edited image>",
        "metadata": {...}
    }
    """
    
    try:
        logger.info("Starting ADDIT processing...")
        
        # Load models (cached after first load)
        load_models()
        
        # Parse input
        job_input = job.get('input', {})
        validate_input(job_input)
        
        # Decode source image
        source_image = decode_image(job_input['source_image'])
        logger.info("Source image decoded successfully")
        
        # Extract parameters with defaults
        prompt_source = job_input['prompt_source']
        prompt_target = job_input['prompt_target']
        subject_token = job_input['subject_token']
        
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
        
        # Encode results
        source_b64 = encode_image(src_image)
        edited_b64 = encode_image(edited_image)
        
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
        
        logger.info("ADDIT processing completed successfully")
        
        return {
            "source_image": source_b64,
            "edited_image": edited_b64,
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        return {
            "error": str(e),
            "status": "failed"
        }

# For local testing
if __name__ == "__main__":
    # Test the handler locally
    import sys
    
    # Create a simple test
    test_input = {
        "source_image": "",  # Add test image base64 here
        "prompt_source": "A photo of a bed in a dark room",
        "prompt_target": "A photo of a dog lying on a bed in a dark room",
        "subject_token": "dog"
    }
    
    result = handler({"input": test_input})
    print(json.dumps(result, indent=2))