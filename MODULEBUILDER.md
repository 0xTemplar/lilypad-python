```markdown
# Lilypad Module Builder SDK Documentation

## Overview
The Lilypad Module Builder SDK provides Python tools for creating, configuring, and deploying AI modules to the Lilypad decentralized compute network. This documentation covers key components and usage patterns.

## Features
- Declarative module configuration
- Automatic Dockerfile generation
- Template-based manifest creation
- Hugging Face integration
- Decorators for common patterns
- Built-in validation and testing

## Installation
```bash
pip install lilypad-sdk
python -m pip install pydantic jinja2 docker
```

## Prerequisites
- Python 3.8+
- Docker Engine
- Lilypad CLI
- Hugging Face account (for model access)

## Quick Start
```python
from lilypad.builder import ModuleConfig, LilypadModuleBuilder

# Initialize module configuration
config = ModuleConfig(
    module_name="my-llm",
    model_repo="tiiuae/falcon-7b-instruct",
    gpu=True,
    min_ram=16000
)

# Build module structure
builder = (LilypadModuleBuilder(config)
          .create_directory_structure()
          .generate_dockerfile()
          .generate_manifest()
          .build_docker_image("user/my-llm:latest"))
```

## Core Components

### 1. ModuleConfig
Configuration model for module specifications:

```python
class ModuleConfig(BaseModel):
    module_name: str  # Required
    module_version: str = "1.0.0"
    gpu: bool = False
    min_cpu: int = 1000  # Millicores
    min_ram: int = 4096  # MB
    base_image: str = "python:3.9-slim"
    model_repo: Optional[str] = None
```

### 2. LilypadModuleBuilder
Main class for module scaffolding:

| Method                 | Description                                  |
|------------------------|----------------------------------------------|
| `create_directory_structure()` | Creates standard module folders        |
| `generate_dockerfile()`         | Generates Dockerfile from template     |
| `generate_manifest()`           | Creates lilypad_module.json.tmpl       |
| `add_dependencies([...])`       | Adds Python requirements               |
| `build_docker_image(tag)`       | Builds and tags Docker image           |

### 3. ModuleDecorators
Decorators for common patterns:

```python
@ModuleDecorators.text_input
@ModuleDecorators.json_output
def process_text(text: str):
    return {"result": text.upper()}
```

## Hugging Face Integration
```python
# Create module from HF model
builder = LilypadModuleBuilder.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    module_name="sdxl-image-gen",
    gpu=True,
    min_ram=24000
)
```

## Docker Integration
```python
# Build and push image
(builder
 .build_docker_image("user/my-module:v1.0", push=True)
 .validate_module())
```

## Testing & Validation
```python
# Validate module structure
if builder.validate_module():
    print("Module valid!")
    
# Test locally
docker run -e MODEL_INPUT="Hello" -v ./outputs:/outputs my-module:v1.0
```

## Advanced Usage

### Custom Templates
Override default templates by creating:
```
templates/
├── Dockerfile.j2
└── module_manifest.j2
```

### CLI Integration (Future)
```bash
lilypad-module create --model tiiuae/falcon-7b --gpu
```

## Examples

### Text Generation Module
```python
config = ModuleConfig(
    module_name="text-generator",
    model_repo="gpt2",
    min_ram=8192
)

builder = (LilypadModuleBuilder(config)
          .add_dependencies(["transformers", "torch"])
          .create_inference_template())
```

### Image Processing Module
```python
config = ModuleConfig(
    module_name="image-processor",
    gpu=True,
    base_image="nvidia/cuda:12.2.0-base"
)

builder = (LilypadModuleBuilder(config)
          .add_dependencies(["torchvision", "pillow"]))
```

## Troubleshooting

### Common Issues
1. **Docker Build Failures**
   - Verify base image compatibility
   - Check platform architecture (linux/amd64)

2. **Missing Files**
   - Run `validate_module()` before building
   - Ensure template files exist

3. **GPU Support**
   - Confirm NVIDIA container toolkit installation
   - Set `gpu=True` in config

## Contributing
1. Fork repository
2. Create feature branch
3. Submit PR with:
   - Updated tests
   - Documentation changes
   - Example modules

## License
MIT License - See [LICENSE](https://opensource.org/licenses/MIT)

---

> **Note**: This documentation assumes Lilypad v0.8+ and Docker 24.0+. Always verify network compatibility with `lilypad check-environment`.