# Contributing to BRIntelcollector

Thank you for taking the time to contribute! This document outlines the process to get started quickly.

## Development Workflow

1. Fork the repository and create your branch from `main`.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run the quality pipeline before submitting changes:
   ```bash
   make lint
   make test
   ```
4. Open a pull request referencing related issues.

## Commit Guidelines

- Use conventional commit messages when possible (e.g. `feat: add rate manager`).
- Include documentation and tests for new features.

## Code Standards

- Python 3.10+
- Format with `black` and lint with `flake8`.
- Ensure `mypy` type checks pass.
- Write docstrings for public functions and classes.

## Reporting Issues

Open an issue with:

- Steps to reproduce the problem
- Expected vs actual behaviour
- Environment details (OS, Python version)

## Code of Conduct

By participating you agree to our [Code of Conduct](CODE_OF_CONDUCT.md).
