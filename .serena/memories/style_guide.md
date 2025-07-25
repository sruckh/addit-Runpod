# Code Style & Conventions for AddIT

## 📏 Code Organization
**File Structure:**
- Private helper functions at top
- Public classes/functions in logical order
- Clear separation of concerns by file

## 🎯 Naming Conventions
**Classes:** PascalCase
- AdditFluxAttnProcessor2_0
- AdditFluxTransformer2DModel

**Functions:** snake_case
- apply_extended_attention()
- img2img_retrieve_latents()
- gaussian_blur()

**Variables:** snake_case
- extended_scale, structure_transfer_step, blend_steps

**Constants:** UPPER_SNAKE_CASE
- Expected for configuration constants

## 📖 Documentation Style
**Docstrings:** Google-style format
```python
def add_object_generated(self, ...):
    """Add object to generated image.
    
    Args:
        prompt_source: Description of source image
        prompt_target: Target image description with object
        subject_token: Object identifier token
    
    Returns:
        tuple: (final_image, attention_maps)
    """
```

**Code Comments:**
- Use # for single-line comments
- Place comments before complex logic
- Explain attention mechanisms in detail

## 🔧 Code Patterns
**Class Structure:**
```python
class AdditFluxAttnProcessor2_0:
    def __init__(self, extended_scale=1.05):
        self.extended_scale = extended_scale
        
    def __call__(self, attn, hidden_states, ...):
        # Core attention processing
        pass
```

**Error Handling:**
- Use try-except blocks for GPU operations
- Provide informative error messages
- Graceful fallback for CPU-only operations

## 🎨 Visual Conventions
**Attention Maps:**
- Use consistent colormaps (jet/plasma)
- Save with descriptive filenames
- Include source/target image overlays

**Output Structure:**
- Save in `outputs/` directory
- Include metadata files
- Consistent naming: `source_description_subject.png`

## 🧪 Scientific Computing Patterns
**Memory Management:**
- Use context managers for GPU tensors
- Clear intermediate variables
- Batch operations when possible

**Reproducibility:**
- Fixed random seeds for demonstrations
- Document all hyperparameters
- Version control for model specifications