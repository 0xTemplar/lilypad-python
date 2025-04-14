
# Contributing Guide

We welcome contributions to the Lilypad Standard Library! Here's how to get started.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/lilypad-sdk.git
   ```
3. Create virtual environment:
   ```bash
   poetry env use python3.11
   poetry shell
   ```
4. Install dependencies:
   ```bash
   poetry install
   eval $(poetry env activate)
   ```

## Coding Standards

- Follow PEP8 guidelines
- Type hints required for all public methods
- 100% test coverage for new features
- Document all public methods with Google-style docstrings
- Keep commits atomic with conventional commit messages

## Testing

Run the full test suite:
```bash
pytest --cov=lilypad --cov-report=term-missing
```

## PR Process

1. Create an issue describing your proposed change
2. Branch from `main` using naming convention:
   ```bash
   git checkout -b feat/my-feature   # For new features
   git checkout -b fix/issue-number  # For bug fixes
   ```
3. Submit PR with:
   - Description of changes
   - Reference to related issues
   - Updated tests and documentation
   - Confirmation of passing CI checks

## Code of Conduct

All contributors must adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to conduct@lilypad.tech.

## Community
<!-- 
Join our development community:
- [Discord Server](https://discord.gg/lilypad)
- [Community Forum](https://forum.lilypad.tech)
- Weekly Office Hours: Wednesdays 3PM UTC -->

## Project Structure

```
lilypad-sdk/
├── lilypad/
│   ├── client.py       # Low-level API client
│   ├── llm.py          # LangChain integration
│   ├── schemas.py      # Pydantic models
│   └── utils.py        # Shared utilities
├── tests/
│   ├── unit/
│   └── integration/
├── docs/               # Documentation source
└── examples/           # Usage examples
```