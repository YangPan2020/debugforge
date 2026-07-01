# Contributing to DebugForge

Thank you for considering contributing to DebugForge! This guide will help you get started.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/YangPan2020/debugforge.git
cd debugforge

# Install in development mode with test dependencies
pip install -e ".[dev]"

# Verify the setup
pytest tests/ -v
```

## Running Tests

Tests use mocked TRACE32 connections and don't require actual hardware:

```bash
# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_config.py -v

# Run with coverage
pytest tests/ --cov=debugforge
```

## Code Style

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/
```

## Adding a New Tool

1. Choose the appropriate module in `src/debugforge/tools/` (or create a new one)
2. Decorate your function with `@mcp.tool()`
3. Write a clear docstring — this becomes the tool description visible to AI agents
4. Add tests in `tests/`
5. If you created a new module, import it in `src/debugforge/server.py`

Example:

```python
from debugforge.server import mcp
from debugforge.state import state

@mcp.tool()
async def my_new_tool(param: str) -> str:
    """Brief description of what this tool does.

    Args:
        param: Description of the parameter

    Returns:
        What the tool returns
    """
    dbg = state.require_connection()
    # Implementation here
    return "result"
```

## Pull Request Process

1. Fork the repository and create a feature branch
2. Make your changes with tests
3. Ensure all tests pass: `pytest tests/ -v`
4. Ensure code passes lint: `ruff check src/ tests/`
5. Write a clear PR description explaining the change
6. Submit the PR against `main`

## Reporting Issues

When reporting bugs, please include:

- DebugForge version (`pip show debugforge`)
- Python version (`python --version`)
- TRACE32 version and target hardware (if relevant)
- Steps to reproduce
- Expected vs actual behavior

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
