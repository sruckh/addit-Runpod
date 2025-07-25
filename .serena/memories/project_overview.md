# AddIT Project Overview

## 🎯 Project Purpose
Add-it is a training-free approach for object insertion in images with pretrained diffusion models. It extends attention mechanisms to seamlessly insert objects into images while maintaining structural consistency and fine details.

## 🏗️ Tech Stack
**Core Technologies:**
- **Python**: 3.11.9 (Anaconda environment)
- **PyTorch**: 2.3.1 with CUDA 12.1
- **Diffusers**: Custom version from HuggingFace
- **Transformers**: 4.44.0
- **Computer Vision**: OpenCV, scikit-image, scipy
- **Data Processing**: NumPy, pandas, pyarrow
- **SAM2**: Meta's Segment Anything Model 2
- **Visualization**: Matplotlib

## 📁 Codebase Structure
**Main Components:**
- **addit_attention_processors.py**: Extended attention processors for FLUX
- **addit_attention_store.py**: Attention storage and management
- **addit_blending_utils.py**: Mask handling and SAM integration
- **addit_flux_pipeline.py**: FLUX pipeline with Add-it integration
- **addit_flux_transformer.py**: Custom transformer blocks
- **addit_methods.py**: Core object insertion methods
- **addit_scheduler.py**: Custom diffusion scheduler
- **run_CLI_addit_*py**: CLI interfaces for real/generated images
- **visualization_utils.py**: Image display and attention visualization

**Key Classes:**
- AdditFluxAttnProcessor2_0: Extended attention processor
- AdditFluxSingleAttnProcessor2_0: Single attention processor
- AdditFluxTransformer2DModel: Custom transformer
- AdditFluxPipeline: Main pipeline implementation
- AttentionStore: Attention storage management