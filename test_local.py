#!/usr/bin/env python3
"""
Local testing script for RunPod serverless ADDIT handler
"""

import json
import base64
import sys
from PIL import Image
import io

def load_test_image(image_path):
    """Load and encode a test image."""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')
    except FileNotFoundError:
        print(f"Test image not found: {image_path}")
        return None

def test_handler():
    """Test the handler locally."""
    try:
        from handler import handler
        
        # Load test image
        test_image = load_test_image("images/bed_dark_room.jpg")
        if not test_image:
            print("Using placeholder image data...")
            # Create a simple placeholder image
            placeholder = Image.new('RGB', (1024, 1024), color='red')
            buffer = io.BytesIO()
            placeholder.save(buffer, format='PNG')
            test_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Test input
        test_input = {
            "source_image": test_image,
            "prompt_source": "A photo of a bed in a dark room",
            "prompt_target": "A photo of a cat lying on a bed in a dark room",
            "subject_token": "cat",
            "seed_src": 6311,
            "seed_obj": 1,
            "extended_scale": 1.1,
            "structure_transfer_step": 4,
            "blend_steps": [18],
            "localization_model": "attention",
            "use_offset": False,
            "use_inversion": True
        }
        
        print("Testing ADDIT handler...")
        result = handler({"input": test_input})
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return False
        
        print("✅ Handler test successful!")
        print(f"Source image size: {len(result['source_image'])} bytes")
        print(f"Edited image size: {len(result['edited_image'])} bytes")
        print(f"Metadata: {json.dumps(result['metadata'], indent=2)}")
        
        # Save test results
        with open("test_result.json", "w") as f:
            json.dump(result, f, indent=2)
        
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_handler()
    sys.exit(0 if success else 1)