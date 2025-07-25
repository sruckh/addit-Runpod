# Essential Commands for AddIT Development

## 🚀 Environment Setup
```bash
# Create environment
conda env create -f environment.yml
conda activate addit

# Install pip dependencies (if additional needed)
pip install -r requirements.txt
```

## 🔧 Development Commands
```bash
# For generated images
python run_CLI_addit_generated.py \
    --prompt_source "description" \
    --prompt_target "description with object" \
    --subject_token "object_name"

# For real images
python run_CLI_addit_real.py \
    --source_image path \
    --prompt_source "description" \
    --prompt_target "description with object" \
    --subject_token "object_name"
```

## 📊 Analysis & Testing
```bash
# Run notebooks for examples
jupyter notebook run_addit_generated.ipynb
jupyter notebook run_addit_real.ipynb

# Basic file operations
python -c "import addit_flux_pipeline; print('Import successful')"

# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"
```

## 🖼️ Quick Examples
```bash
# Add a cat to a bedroom
python run_CLI_addit_real.py \
    --source_image images/bed_dark_room.jpg \
    --prompt_source "a photo of a bed in a dark room" \
    --prompt_target "a photo of a cat sleeping on a bed in a dark room" \
    --subject_token "cat"

# Add hat to generated cat
python run_CLI_addit_generated.py \
    --prompt_source "a photo of a cat sitting on the couch" \
    --prompt_target "a photo of a cat wearing a red hat sitting on the couch" \
    --subject_token "hat"
```