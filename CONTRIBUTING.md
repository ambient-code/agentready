# Contributing Guidelines

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv)
- Git

#### Installing uv

**macOS (Homebrew):**
```bash
brew install uv
```

**Fedora 40+ (dnf):**
```bash
dnf install uv
```

**Other platforms:**
```bash
# Using pip
pip install uv
```

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/agentready.git
   cd agentready
   ```

3. Set up your development environment:
   ```bash
   # Using uv (recommended)
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev]"

   ```

4. Add the upstream remote (to sync with the original repository):
   ```bash
   git remote add upstream https://github.com/ambient-code/agentready.git
   git fetch upstream
   ```

5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

### Creating a Feature Branch

Always create a new branch for your work:

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/add-new-api`
- `fix/resolve-crash-on-startup`
- `docs/improve-installation-guide`

### Making Changes

1. Write clear, concise code
2. Follow the project's coding standards
3. Add tests for new functionality
4. Update documentation as needed
5. Run linters and tests before committing

### Running Tests

The project uses pytest for testing. You can run tests using make or directly with pytest:

```bash
# Run all tests (recommended)
make test

# Run tests with coverage report
make test-coverage

# Or run pytest directly
pytest

# Run specific test file
pytest tests/unit/cli/test_main.py

# Run specific test class or function
pytest tests/unit/cli/test_main.py::TestRunAssessment
pytest tests/unit/cli/test_main.py::TestRunAssessment::test_run_assessment_function

# Run with verbose output
pytest -v

# Run only unit tests
pytest tests/unit/

# Run only e2e tests
pytest tests/e2e/
```

### Code Style

We use the following tools to maintain code quality:

- **black** - Code formatting
- **isort** - Import sorting
- **ruff** - Linting

```bash
# Run all linters (check only)
make lint

# Auto-format code
make format

# Or run tools individually
black src/ tests/
isort src/ tests/
ruff check src/ tests/
```


### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(api): add user authentication endpoint

fix(parser): resolve crash when parsing empty files

docs(readme): update installation instructions
```

### Pull Request Process

1. **Update your branch** with the latest changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push your changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create a Pull Request**:
   - Use the PR template
   - Provide a clear description
   - Link related issues
   - Request reviews from maintainers

4. **Address feedback**:
   - Respond to review comments
   - Make requested changes
   - Push updates to your branch

5. **Wait for approval**:
   - At least one maintainer approval required
   - All CI checks must pass
   - No merge conflicts

## Testing Guidelines

- Write tests for all new functionality
- Maintain or improve code coverage
- Include both positive and negative test cases
- Test edge cases and error conditions

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions and classes
- Update API documentation if applicable
- Add examples for new features

## Issue Reporting

When reporting issues, please include:

- Clear, descriptive title
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, version, etc.)
- Error messages or logs
- Screenshots if applicable

## Questions?

If you have questions:
- Check existing issues and discussions
- Ask in pull request comments
- Open a new discussion
- Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing! 🎉
