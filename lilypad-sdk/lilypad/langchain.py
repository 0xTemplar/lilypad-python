
from utils import SUPPORTED_MODELS

import pydantic
from typing import Any, Optional, Union

import pydantic
from langchain_core.exceptions import OutputParserException
from langchain_core.language_models.base import LanguageModelInput
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.rate_limiters import BaseRateLimiter
from langchain_core.runnables.base import Runnable
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI
from lilypad.client import LilypadClient




class LilypadLLMWrapper(Runnable):
    def __init__(
        self,
        provider: str = "lilypad",
        model: str = "llama3.1:8b",
        temperature: float = 0.0,
        max_tokens: int = 8192,
        rate_limiter: Union[BaseRateLimiter, None] = None,
        api_key: str = "",
    ):
        self.provider = provider
        self.model = model
        self.temperature = temperature
        self.api_key = api_key
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
            api_key=self.api_key,
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