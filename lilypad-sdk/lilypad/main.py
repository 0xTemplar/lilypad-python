from app.core import LILYPAD_API_KEY
import json
import logging
import pydantic
import requests
from typing import Any, Dict, List, Optional, Union

import pydantic
from langchain_core.exceptions import OutputParserException
from langchain_core.language_models.base import LanguageModelInput
from langchain_core.messages import BaseMessage, SystemMessage, ChatMessage
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.rate_limiters import BaseRateLimiter
from langchain_core.runnables.base import Runnable
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI

# List of approved models based on the documentation response JSON.
SUPPORTED_MODELS = {
    "deepscaler:1.5b",
    "gemma3:4b",
    "llama3.1:8b",
    "llava:7b",
    "mistral:7b",
    "openthinker:7b",
    "phi4-mini:3.8b",
    "deepseek-r1:7b",
    "phi4:14b",
    "qwen2.5:7b",
    "qwen2.5-coder:7b",
}


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


class LilypadLLMWrapper(Runnable):
    def __init__(
        self,
        provider: str = "lilypad",
        model: str = "llama3.1:8b",
        temperature: float = 0.0,
        max_tokens: int = 8192,
        rate_limiter: Union[BaseRateLimiter, None] = None,
    ):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.rate_limiter = rate_limiter
        self.parser = StrOutputParser()
        self.schema = None

        # Validate supported models
        self.supported_models = [
            "deepscaler:1.5b", "gemma3:4b", "llama3.1:8b", "llava:7b",
            "mistral:7b", "openthinker:7b", "phi4-mini:3.8b",
            "deepseek-r1:7b", "phi4:14b", "qwen2.5:7b", "qwen2.5-coder:7b"
        ]
        
        if self.model not in self.supported_models:
            raise ValueError(f"Unsupported Lilypad model: {self.model}")

        # Initialize ChatOpenAI with Lilypad configuration
        self.llm = ChatOpenAI(
            base_url="https://anura-testnet.lilypad.tech/api/v1",
            api_key=LILYPAD_API_KEY,
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            # model_kwargs={
            #     'headers': {
            #         'Authorization': f'Bearer {LILYPAD_API_KEY}',
            #         'X-Lilypad-Provider': 'custom'  # Custom header for Lilypad
            #     }
            # }
        )


    def coerce_to_schema(self, llm_output: str):
        """
        Coerce raw LLM output into a structured schema object.
        """
        if not self.schema:
            raise ValueError("Schema is not defined.")

        schema_class_name = self.schema.__name__
        if schema_class_name == "Question":
            schema_field_name = "question"
        elif schema_class_name == "Answer":
            schema_field_name = "answer"
        else:
            raise OutputParserException(
                f"Unable to coerce output to schema: {schema_class_name}",
                llm_output=llm_output,
            )
        schema_values = {schema_field_name: llm_output}
        pydantic_object = self.schema(**schema_values)
        return pydantic_object

    
    def invoke(
        self,
        input: LanguageModelInput,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> BaseMessage:
        """
        Invoke the LLM with the given input and configuration.
        """
        prompt = input

        # Example: for providers like Google, one might inject formatting instructions.
        if self.provider == "google" and self.schema is not None:
            format_instructions = self.parser.get_format_instructions()
            messages = input.to_messages()
            messages[0] = SystemMessage(content=f"{messages[0].content}\n{format_instructions}")
            prompt = ChatPromptValue(messages=messages)

        try:
            return self.llm.invoke(input=prompt, config=config)
        except OutputParserException as ex:
            return self.coerce_to_schema(ex.llm_output)

    def with_structured_output(self, schema: pydantic.BaseModel):
        """
        Configure the LLM wrapper to output structured data using a Pydantic schema.
        """
        if self.provider == "lilypad":
            self.llm = self.llm.with_structured_output(schema)
        return self



def get_fast_llm(rate_limiter: BaseRateLimiter | None = None):
    """Get a fast-responding model optimized for quick interactions"""
    return LilypadLLMWrapper(
        model="llama3.1:8b",
        temperature=0.3,
        rate_limiter=rate_limiter
    )

def get_long_context_llm(rate_limiter: BaseRateLimiter | None = None):
    """Get a model optimized for large context windows"""
    return LilypadLLMWrapper(
        model="phi4:14b",
        temperature=0.1,
        max_tokens=16384,  # Adjust based on model capabilities
        rate_limiter=rate_limiter
    )

def get_vision_llm(rate_limiter: BaseRateLimiter | None = None):
    """Get a multimodal vision-language model"""
    return LilypadLLMWrapper(
        model="llava:7b",
        # model="gemma3:4b",
        temperature=0.2,
        rate_limiter=rate_limiter
    )

def get_code_llm(rate_limiter: BaseRateLimiter | None = None):
    """Get a model optimized for code generation"""
    return LilypadLLMWrapper(
        model="qwen2.5-coder:7b",
        temperature=0.4,
        rate_limiter=rate_limiter
    )


if __name__ == "__main__":
    # For general purpose chat
    llm = get_long_context_llm()

    class Joke(pydantic.BaseModel):
        setup: str
        punchline: str

    structured_llm = llm.with_structured_output(Joke)
    joke = structured_llm.invoke("Tell me a science joke")
    print(f"{joke.punchline}\n{joke.setup}")



    # # For image understanding 
    # vision_llm = get_vision_llm()
    # description = vision_llm.invoke({
    #     "text": "Describe this image",
    #     "image": "<base64-encoded-image>"
    # })