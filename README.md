
# Lilypad Standard Library

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

The Lilypad Standard Library provides Python tools for interacting with Lilypad's decentralized compute network. Designed for both AI developers and blockchain enthusiasts, it offers seamless integration with LangChain and direct access to Lilypad's core capabilities.

## Features

- 🧠 **AI Model Integration**: Access cutting-edge models (LLaMA, Mistral, Phi, etc.) through decentralized infrastructure
- ⛓️ **LangChain Compatibility**: Use as drop-in replacement for OpenAI clients in existing LangChain workflows
- 🌐 **Dual Interface**: Choose between high-level LangChain API or direct low-level client access
- 🖼️ **Multimodal Support**: Text generation, image synthesis, and experimental vision-language models
- 🔍 **Job Management**: Track compute jobs and retrieve results programmatically

## Supported Models
```python
[
    "deepscaler:1.5b", "gemma3:4b", "llama3.1:8b",
    "llava:7b", "mistral:7b", "openthinker:7b",
    "phi4-mini:3.8b", "deepseek-r1:7b", "phi4:14b",
    "qwen2.5:7b", "qwen2.5-coder:7b"
]
```

## Installation

```bash
pip install lilypad-sdk
```

## Quick Start

### Basic Usage
```python
from lilypad import get_llm

llm = get_llm(model="mistral:7b")
response = llm.invoke("Explain quantum entanglement simply")
print(response.content)
```

### Image Generation
```python
image_bytes = llm.client.generate_image(
    "Cyberpunk frog hacker in neon-lit swamp",
    model="sdxl-turbo"
)
with open("hacker_frog.png", "wb") as f:
    f.write(image_bytes)
```

### LangChain Integration
```python
from langchain_core.prompts import ChatPromptTemplate
from lilypad import get_fast_llm

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant"),
    ("human", "{input}")
])

chain = prompt | get_fast_llm()
print(chain.invoke({"input": "Explain blockchain in pirate terms"}))
```

## Documentation

Full documentation available at [docs.lilypad.tech](https://docs.lilypad.tech)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License

<!-- ## Contact

- Discord: [lilypad-channel](https://discord.gg/lilypad)
- Email: dev@lilypad.tech -->

