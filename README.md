# Tabs Private Agent

A small, local multi-agent coding team powered by [Ollama](https://ollama.com/) and `qwen2.5-coder:7b`.

The project runs entirely on your computer. It makes no cloud model API calls and needs no API key.

## How it works

You describe a coding task in ordinary language. Three agents pass the work down a simple hierarchy:

1. **CEO** receives the goal and delegates it to the director.
2. **Director** turns the goal into a concrete implementation task.
3. **Manager** creates or reads project files and runs `pytest` to verify the result.

The manager is restricted to the project directory, so it cannot write to paths outside this repository.

## Prerequisites

- [Ollama](https://ollama.com/) installed and running
- Python 3.10 or newer

Download the local coding model once:

```bash
ollama pull qwen2.5-coder:7b
```

## Installation

Clone this repository, then create a virtual environment and install the Python dependencies:

```bash
git clone https://github.com/tabishsyed777/tabz-private-agent-.git
cd tabz-private-agent-
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run the agent company

```bash
python company.py
```

Example task:

```text
Create divide.py with a divide(a, b) function. Raise ValueError when b is zero, and add pytest tests.
```

The program prints each delegation and tool call, then gives a final status.

## Verify generated code

Run the project test suite at any time:

```bash
pytest -q
```

## Important notes

- This is a learning project, not a production-grade autonomous coding system.
- Review generated code before using it in an important project.
- The model is downloaded locally by Ollama; it is deliberately not included in this repository.
- `qwen2.5-coder:7b` can occasionally express tool calls as JSON text. `company.py` includes a compatibility fallback for that behavior.

## Model and license

This repository contains the agent code, not Qwen or Ollama. The `Qwen2.5-Coder-7B-Instruct` model is published by Qwen under Apache 2.0; see its [official model card and license](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct) for the applicable terms.

Choose a license for this repository before publishing (for example, MIT) if you want others to reuse your code.
