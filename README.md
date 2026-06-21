# refund_graph_AI

## Project Initialization

This project uses Poetry for dependency and environment management.
The required Python version is 3.13.

### 1. Prerequisites

Check Python version:

```bash
python3 --version
```

Install Poetry (if not installed):

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Verify Poetry:

```bash
poetry --version
```

### 2. Set Python 3.13 for this project

If your system has multiple Python versions, point Poetry to 3.13 explicitly:

```bash
poetry env use python3.13
```

### 3. Install dependencies

From the project root directory:

```bash
poetry install
```

This demo uses a local Ollama server. Before running the workflow, make sure Ollama is available at `http://localhost:11434` and that a `qwen`-based model has been pulled locally.

### 4. Run the demo entrypoint

```bash
poetry run refund-graph-ai
```

### 5. Run tests

```bash
poetry run pytest
```

### 6. Optional: run lint checks

```bash
poetry run ruff check .
```
