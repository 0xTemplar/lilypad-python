from utils import SUPPORTED_MODELS 

import json
import requests
from typing import Any, Dict, List, Optional, Union





class LilypadClient:
    """
    A client that encapsulates all key Lilypad endpoints:
      - Chat completions (streaming and non-streaming)
      - Image generation
      - Job status tracking
      - Cowsay jobs

    This client uses the Lilypad base URL and API key for all requests.
    """

    def __init__(self, api_key: str, base_url: str = "https://anura-testnet.lilypad.tech/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def get_available_models(self) -> List[str]:
        """Call the GET /models endpoint to retrieve a list of available models."""
        url = f"{self.base_url}/models"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise RuntimeError(f"Error fetching models: {response.status_code} {response.text}")
        result = response.json()
        # Result is expected to be like: {"data": {"models": [ ... ]}, ...}
        return result.get("data", {}).get("models", [])

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.6,
        stream: bool = False,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Invoke the Chat Completion endpoint.
        Supports both streaming (SSE) and a one-shot response.

        Args:
            messages: A list of messages (each a dict with keys "role" and "content")
            model: The model identifier (must be in SUPPORTED_MODELS)
            temperature: Controls randomness
            stream: Use streaming mode if True

        Returns:
            When not streaming, a dict following the OpenAI chat completion format.
            When streaming, a list of chunk objects.
        """
        if model not in SUPPORTED_MODELS:
            raise ValueError(f"Model '{model}' is not supported. Supported models: {SUPPORTED_MODELS}")

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if stream:
            payload["stream"] = True

        response = requests.post(url, headers=self.headers, json=payload, stream=stream)
        if response.status_code != 200:
            raise RuntimeError(f"Chat completion error: {response.status_code} {response.text}")

        if stream:
            # For streaming responses we read chunks as server-sent events
            chunks = []
            for line in response.iter_lines(decode_unicode=True):
                if line.strip() == "data: [DONE]":
                    break
                # Many lines start with 'data: ' so remove that
                if line.startswith("data: "):
                    line = line[len("data: "):]
                if line:
                    chunk = json.loads(line)
                    chunks.append(chunk)
            return chunks

        return response.json()

    def get_image_models(self) -> List[str]:
        """Retrieve the list of supported image generation models."""
        url = f"{self.base_url}/image/models"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise RuntimeError(f"Error fetching image models: {response.status_code} {response.text}")
        result = response.json()
        return result.get("data", {}).get("models", [])

    def generate_image(self, prompt: str, model: str, output_file: Optional[str] = None) -> bytes:
        """
        Generate an image via the image generation endpoint.

        Args:
            prompt: The image prompt (max 1000 characters)
            model: The model to use (e.g. "sdxl-turbo")
            output_file: Optional; if provided, writes the raw bytes to a file.

        Returns:
            The raw bytes of the generated image.
        """
        url = f"{self.base_url}/image/generate"
        payload = {"prompt": prompt, "model": model}
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Image generation error: {response.status_code} {response.text}")
        image_bytes = response.content
        if output_file:
            with open(output_file, "wb") as f:
                f.write(image_bytes)
        return image_bytes

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Retrieve the status and details of a job using its ID.

        Args:
            job_id: The job identifier.
        """
        url = f"{self.base_url}/jobs/{job_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise RuntimeError(f"Job status error: {response.status_code} {response.text}")
        return response.json()

    def cowsay(self, message: str) -> Dict[str, Any]:
        """
        Start a new cowsay job with the given message.

        Returns:
            A dict that includes the job id for later retrieval.
        """
        url = f"{self.base_url}/cowsay"
        payload = {"message": message}
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"Cowsay job error: {response.status_code} {response.text}")
        return response.json()

    def get_cowsay_results(self, job_id: str) -> Dict[str, Any]:
        """
        Retrieve the results of a cowsay job.
        """
        url = f"{self.base_url}/cowsay/{job_id}/results"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise RuntimeError(f"Cowsay results error: {response.status_code} {response.text}")
        return response.json()