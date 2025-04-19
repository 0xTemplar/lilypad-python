import os
import json
import docker
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from jinja2 import Environment, FileSystemLoader

from lilypad.module_builder.config import ModuleConfig


class LilypadModuleBuilder:
    """Main class for building Lilypad modules"""
    
    def __init__(self, config: ModuleConfig):
        self.config = config
        self.template_env = Environment(
            loader=FileSystemLoader(Path(__file__).parent / 'templates'),
            keep_trailing_newline=True
        )
        self.module_dir = Path(f"modules/{self.config.module_name}")
        self.docker_client = docker.from_env()
        
    def create_directory_structure(self):
        """Create standard module directory structure"""
        dirs = [
            self.module_dir / 'src',
            self.module_dir / 'models',
            self.module_dir / 'tests'
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            
        return self
    
    def generate_dockerfile(self):
        """Generate Dockerfile from template"""
        template = self.template_env.get_template('Dockerfile.j2')
        context = {
            'base_image': self.config.base_image,
            'platform': self.config.platform,
            'gpu': self.config.gpu
        }
        
        dockerfile_content = template.render(context)
        (self.module_dir / 'Dockerfile').write_text(dockerfile_content)
        return self
    
    def generate_manifest(self):
        """Generate lilypad_module.json.tmpl"""
        template = self.template_env.get_template('module_manifest.j2')
        manifest_content = template.render(self.config.model_dump())
        (self.module_dir / 'lilypad_module.json.tmpl').write_text(manifest_content)
        return self
    
    def add_dependencies(self, requirements: List[str]):
        """Add Python dependencies to requirements.txt"""
        req_file = self.module_dir / 'requirements.txt'
        req_file.write_text('\n'.join(requirements))
        return self
    
    def add_model_download_script(self):
        """Generate model download script for Hugging Face models"""
        if self.config.model_repo:
            template = self.template_env.get_template('download_model.j2')
            script_content = template.render({
                'model_repo': self.config.model_repo,
                'local_path': './models'
            })
            (self.module_dir / 'src/download_model.py').write_text(script_content)
        return self
    
    def create_inference_template(self):
        """Create base inference script template"""
        template = self.template_env.get_template('inference_script.j2')
        script_content = template.render({
            'model_name': self.config.model_name,
            'gpu': self.config.gpu
        })
        (self.module_dir / 'src/run_inference.py').write_text(script_content)
        return self
    
    def build_docker_image(self, tag: str, push: bool = False):
        """Build and optionally push Docker image"""
        client = docker.APIClient()
        build_args = {
            'MODEL_REPO': self.config.model_repo,
            'MODEL_NAME': self.config.model_name
        }
        
        stream = client.build(
            path=str(self.module_dir),
            tag=tag,
            buildargs=build_args,
            platform=self.config.platform,
            rm=True
        )
        
        for line in stream:
            print(line.decode('utf-8').strip())
            
        if push:
            self.docker_client.images.push(tag)
            
        return self
    
    def validate_module(self):
        """Validate module structure"""
        required_files = [
            'Dockerfile',
            'lilypad_module.json.tmpl',
            'src/run_inference.py'
        ]
        
        missing = [f for f in required_files if not (self.module_dir / f).exists()]
        if missing:
            raise ValueError(f"Missing required files: {missing}")
            
        return True
    
    @classmethod
    def from_pretrained(cls, model_repo: str, **kwargs):
        """Convenience method for HF models"""
        config = ModuleConfig(
            model_repo=model_repo,
            model_name=model_repo.split('/')[-1],
            **kwargs
        )
        return cls(config)


# Example Usage
if __name__ == "__main__":
    # Create a module for Falcon-7B
    config = ModuleConfig(
        module_name="falcon-7b-chat",
        model_repo="tiiuae/falcon-7b-instruct",
        gpu=True,
        min_ram=16000
    )
    
    builder = (
        LilypadModuleBuilder(config)
        .create_directory_structure()
        .generate_dockerfile()
        .generate_manifest()
        .add_dependencies([
            'transformers==4.36.0',
            'torch==2.1.0',
            'accelerate==0.25.0'
        ])
        .add_model_download_script()
        .create_inference_template()
        .build_docker_image("username/falcon-7b-chat:latest")
    )
    
    print("Module created successfully!")