# AddIT System Architecture

## 🏗️ Core Architecture Overview

AddIT extends FLUX diffusion models with custom attention mechanisms for object insertion without training. The system operates in three domains:
1. **Source Space**: Original image features and semantics
2. **Target Space**: Desired final image with new object
3. **Attention Space**: Extended attention for seamless blending

## 🔗 System Flow

```
Input: (source_image OR prompt_source) 
   ↓
Extended Attention Processing ←→ Object Detection (SAM2)
   ↓
Blending with Structure Transfer
   ↓
Output: Target image with inserted object
```

## 🧩 Key Components Architecture

### 1. Extended Attention System
**Location:** addit_attention_processors.py
- **AdditFluxAttnProcessor2_0**: Multi-head extended attention with weighted blending
- **AdditFluxSingleAttnProcessor2_0**: Simplified single-stream attention
- **apply_extended_attention()**: Core attention computation and weighting

### 2. Object Localization
**Location:** addit_blending_utils.py
- **clipseg_predict()**: CLIP-based object detection
- **grounding_sam_predict()**: Grounded SAM for segment anything
- **attention_*_sam_predict()**: Various SAM integration modes

### 3. FLUX pijpeline Integration
**Location:** addit_flux_pipeline.py
- **AdditFluxPipeline**: Wrapped FLUX with custom attention processors
- **register_my_attention_processors()**: Processor registration mechanism
- **img2img_retrieve_latents()**: Image-to-image latent space conversion

### 4. Custom Transformer Blocks
**Location:** addit_flux_transformer.py
- **AdditFluxTransformerBlock**: Extended transformer with attention hooks
- **AdditFluxSingleTransformerBlock**: Single-stream variant
- **EmbedND**: Enhanced positional embedding

### 5. Attention Storage & Management
**Location:** addit_attention_store.py
- **AttentionStore**: Central storage for attention matrices
- **visualize_tokens_attentions()**: Attention visualization utilities

## 🎯 Integration Points

### Image Modes
1. **Real Image Mode**: PC2R inference on existing images
2. **Generated Image Mode**: FLUX generation with object insertion

### Neural Attention Layers
- Layer 0-7: Standard FLUX attention
- Layer 8-14: Extended attention with object blending
- Layer 15-19: Final blending and consistency

### Parameter Controls
- **extended_scale**: 1.05-1.2 (attention expansion)
- **structure_transfer_step**: 2-8 (blending intensity)
- **blend_steps**: specific timesteps for object injection