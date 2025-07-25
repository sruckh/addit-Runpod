#!/usr/bin/env python3
"""
Pre-load FLUX.1-dev models during Docker build to eliminate cold start delays.
"""

import os
import torch
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def preload_models():
    """Pre-load FLUX.1-dev models and cache them."""
    try:
        # Import after requirements are installed
        from diffusers import FluxPipeline
        
        logger.info('🔄 Pre-loading FLUX.1-dev models...')
        
        # Get HF token if available (not required for caching, but might be needed for gated models)
        hf_token = os.getenv('HF_TOKEN')
        if hf_token:
            logger.info('Using HF_TOKEN for model authentication')
        
        # Load pipeline with caching
        pipe = FluxPipeline.from_pretrained(
            'black-forest-labs/FLUX.1-dev', 
            torch_dtype=torch.bfloat16, 
            cache_dir='/app/.cache/huggingface',
            token=hf_token
        )
        logger.info('✅ FLUX.1-dev pipeline loaded successfully')
        
        # Move to device (CPU during build, but test the capability)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        pipe.to(device)
        logger.info(f'✅ Models moved to {device} and cached')
        
        # Clean up memory
        del pipe
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info('✅ Model pre-loading complete - ready for serverless deployment')
        return True
        
    except ImportError as e:
        logger.error(f'⚠️ Missing dependencies for model pre-loading: {e}')
        logger.warning('⚠️ Install requirements.txt dependencies first')
        return False
    except Exception as e:
        logger.error(f'⚠️ Model pre-loading failed: {e}')
        logger.warning('⚠️ Will fallback to lazy loading on first request')
        return False

if __name__ == '__main__':
    preload_models()