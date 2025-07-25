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
from typing import Dict, Any, Tuple, Optional

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

def generate_prompt_with_qwen(image_base64: str, object_to_add: str) -> Tuple[str, str]:
    """
    Generate prompt_source and subject_token using Qwen2.5-VL-72B (free) via OpenRouter.
    
    Args:
        image_base64: Base64 encoded source image
        object_to_add: Object to add to the image (e.g., "cat", "flower", "car")
    
    Returns:
        Tuple of (prompt_source, subject_token)
    """
    try:
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if not openrouter_key:
            logger.warning("OPENROUTER_API_KEY not found, using fallback prompts")
            return f"A photo with a {object_to_add}", object_to_add
        
        # Prepare the API request
        headers = {
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Analyze this image and describe what you see. Focus on:
1. The main subject/scene
2. The environment/setting 
3. The lighting and mood
4. Objects already present

Then suggest where a {object_to_add} could naturally fit in this scene.

Respond with ONLY this format:
DESCRIPTION: [your detailed description of the image]
SUBJECT_TOKEN: {object_to_add}"""

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
            description = ""
            subject_token = object_to_add
            
            for line in lines:
                if line.startswith("DESCRIPTION:"):
                    description = line.replace("DESCRIPTION:", "").strip()
                elif line.startswith("SUBJECT_TOKEN:"):
                    subject_token = line.replace("SUBJECT_TOKEN:", "").strip()
            
            prompt_source = description if description else f"A photo with a {object_to_add}"
            logger.info(f"Generated prompt_source: {prompt_source}")
            logger.info(f"Generated subject_token: {subject_token}")
            
            return prompt_source, subject_token
        else:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            return f"A photo with a {object_to_add}", object_to_add
            
    except Exception as e:
        logger.error(f"Error generating prompt with Qwen: {str(e)}")
        return f"A photo with a {object_to_add}", object_to_add

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

def validate_input(job_input: Dict[str, Any]) -> None:
    """Validate the input parameters."""
    # Source image is always required
    if 'source_image' not in job_input:
        raise ValueError("Missing required field: source_image")
    
    # For auto-prompt generation, we need object_to_add
    # For manual prompts, we need prompt_source, prompt_target, subject_token
    has_auto_prompt = 'object_to_add' in job_input
    has_manual_prompts = all(field in job_input for field in ['prompt_source', 'prompt_target', 'subject_token'])
    
    if not has_auto_prompt and not has_manual_prompts:
        raise ValueError("Either provide 'object_to_add' for auto-generation or 'prompt_source', 'prompt_target', 'subject_token' for manual mode")
    
    # If manual prompts provided, validate subject token appears in target prompt
    if has_manual_prompts:
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
        
        # Handle auto-prompt generation vs manual prompts
        if 'object_to_add' in job_input:
            # Auto-generate prompts using Qwen2.5-VL
            logger.info(f"Auto-generating prompts for object: {job_input['object_to_add']}")
            prompt_source, subject_token = generate_prompt_with_qwen(
                job_input['source_image'], 
                job_input['object_to_add']
            )
            prompt_target = job_input.get('prompt_target', 
                f"{prompt_source.replace('A photo', f'A photo of a {subject_token}')}")
        else:
            # Use manually provided prompts
            prompt_source = job_input['prompt_source']
            prompt_target = job_input['prompt_target'] 
            subject_token = job_input['subject_token']
            logger.info("Using manually provided prompts")
        
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