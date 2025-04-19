from typing import Optional
from pydantic import BaseModel, Field

class ModuleConfig(BaseModel):
    """Configuration model for Lilypad modules"""
    module_name: str = Field(..., description="Unique name for the module")
    module_version: str = "1.0.0"
    description: str = "Custom Lilypad Module"
    author: str = "Anonymous"
    license: str = "MIT"
    
    # Hardware requirements
    gpu: bool = False
    min_cpu: int = 1000  # In millicores
    min_ram: int = 4096  # In MB
    
    # Docker configuration
    base_image: str = "python:3.9-slim"
    platform: str = "linux/amd64"
    
    # Model configuration
    model_name: Optional[str] = None
    model_repo: Optional[str] = None
    
    # Runtime configuration
    timeout: int = 600  # Seconds
    concurrency: int = 1