# Essential Commands Reference

## 🚀 Setup Commands
```bash
# Environment setup
conda env create -f environment.yml
conda activate addit

# Verify installation
python -c "import torch; print(torch.cuda.is_available())"
python -c "import diffusers; print('✅ Diffusers installed')"
```

## 📸 Image Processing Commands

### Real Images
```bash
python run_CLI_addit_real.py \
    --source_image images/cat.jpg \
    --prompt_source "a photo of a cat" \
    --prompt_target "a photo of a cat wearing a red bowtie" \
    --subject_token "bowtie" \
    --output_dir outputs/ \
    --show_attention
```

### Generated Images  
```bash
python run_CLI_addit_generated.py \
    --prompt_source "a modern kitchen" \
    --prompt_target "a modern kitchen with a golden retriever" \
    --subject_token "golden retriever" \
    --extended_scale 1.1 \
    --structure_transfer_step 4
```

## 🧪 Testing & Validation
```bash
# Test core functionality
python -c "from addit_flux_pipeline import AdditFluxPipeline; print('✅ Pipeline loaded')"

# Test SAM2 integration
python -c "from addit_blending_utils import grounding_sam_predict; print('✅ SAM2 ready')"

# Test attention processors
python -c "from addit_attention_processors import AdditFluxAttnProcessor2_0; print('✅ Processors ready')"

# Test visualization
python -c "from visualization_utils import show_images; print('✅ Visualization ready')"
```

## 📊 Jupyter Notebooks
```bash
jupyter notebook run_addit_generated.ipynb
jupyter notebook run_addit_real.ipynb
```

## 🎯 Quick Debug Commands
```bash
# Check GPU memory
nvidia-smi

# Check Python packages
conda list | grep -E "(torch|diffusers|transformers)"

# Test CUDA
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0)}')"

# Memory usage test
python -c "
import torch
print(f'Memory allocated: {torch.cuda.memory_allocated()/1024**3:.2f}GB')
print(f'Memory reserved: {torch.cuda.memory_reserved()/1024**3:.2f}GB')
"
```

## 🔄 Development Workflow
```bash
# Start with small test
python run_CLI_addit_real.py \
    --source_image images/cat.jpg \
    --prompt_source "a cat" \
    --prompt_target "a cat with sunglasses" \
    --subject_token "sunglasses" \
    --structure_transfer_step 2

# Scale up
python run_CLI_addit_generated.py \
    --prompt_source "a serene garden" \
    --prompt_target "a serene garden with a fountain" \
    --subject_token "fountain" \
    --extended_scale 1.2 \
    --show_attention
```

## 🛠️ System Commands
```bash
# File operations
ls -la images/
mkdir -p outputs/experiments/
find . -name "*.py" | head -10

# GPU monitoring
watch -n 1 nvidia-smi

# Environment info
conda info --envs
python --version
gcc --version
```