# publisher.py

import subprocess
from pathlib import Path
from typing import Dict, Any
import json
import logging

class ModulePublisher:
    """Handles publishing and testing Lilypad modules"""
    
    def __init__(self, builder):
        self.builder = builder
        self.logger = logging.getLogger(__name__)
        
    def publish_to_ipfs(self) -> str:
        """Publish module to IPFS and return CID"""
        try:
            result = subprocess.run(
                ["lilypad", "publish", str(self.builder.module_dir)],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self.logger.error(f"IPFS publish failed: {e.stderr}")
            raise

    def run_local_test(self, inputs: Dict[str, str]) -> Dict[str, Any]:
        """Run local test of the module"""
        test_output_dir = self.builder.module_dir / "test_outputs"
        test_output_dir.mkdir(exist_ok=True)

        env_vars = [
            f"-e {k}={v}" for k, v in inputs.items()
        ]
        
        cmd = [
            "docker", "run", "--rm",
            *env_vars,
            "-v", f"{test_output_dir.absolute()}:/outputs",
            f"{self.builder.config.module_name}:latest"
        ]
        
        try:
            subprocess.run(cmd, check=True)
            with open(test_output_dir / "results.json") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Local test failed: {str(e)}")
            raise

    def deploy_to_lilypad(self, network: str = "testnet"):
        """Deploy module to Lilypad network"""
        if not self.builder.validate_module():
            raise ValueError("Module validation failed")
            
        print(f"Deploying {self.builder.config.module_name} to {network}:")
        print("1. Building and pushing Docker image...")
        self.builder.build_docker_image(
            f"{self.builder.config.module_name}:latest",
            push=True
        )
        
        print("2. Publishing to IPFS...")
        cid = self.publish_to_ipfs()
        
        print("3. Registering on Lilypad...")
        try:
            subprocess.run([
                "lilypad", "register-module",
                "--cid", cid,
                "--network", network
            ], check=True)
            print(f"Successfully deployed module CID: {cid}")
            return cid
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Registration failed: {str(e)}")
            raise