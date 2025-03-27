# Internal Development Guidelines for Chip Swinger Championship Poker Trainer

This document provides guidelines for authorized developers contributing to the proprietary Chip Swinger Championship Poker Trainer project. This is a closed-source, proprietary project. Access to this codebase requires explicit authorization from the project owner.

## Development Workflow

1. Receive task assignment from issue tracker
2. Create a new branch: `feature/[issue-number]-[brief-description]`
3. Make implementation changes
4. Write and run tests
5. Commit changes with descriptive messages
6. Push branch and create a pull request

## Branch Naming Convention

- Use `feature/` prefix for new features
- Use `fix/` prefix for bug fixes
- Use `docs/` prefix for documentation changes
- Use `refactor/` prefix for code refactoring
- Use `test/` prefix for adding or updating tests

Example: `feature/42-implement-hand-evaluator`

## Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Include the issue number in the commit message
- Provide a clear description of changes

Example:
```
[#42] Add hand evaluator implementation

- Implement hand ranking algorithm
- Support all poker hand combinations
- Add unit tests for edge cases
```

## Pull Request Requirements

1. Reference the issue number in the PR title: `[Issue #42] Implement hand evaluator`
2. Include a detailed description of the implementation approach
3. Ensure all tests pass
4. Update documentation as necessary
5. Follow code style guidelines

## Coding Standards

### Python Style Guide

- Follow PEP 8
- Use type annotations
- Write comprehensive docstrings
- Maintain test coverage

### JavaScript/TypeScript Style Guide

- Follow Airbnb JavaScript Style Guide
- Use ESLint and Prettier for formatting
- Prefer functional components in React
- Use TypeScript interfaces for type safety

## Testing Requirements

- Write unit tests for all new functionality
- Implement integration tests for component interactions
- Test edge cases and error conditions
- Verify performance for computationally intensive operations

## Problem-Solving Approach

When tackling complex problems or debugging issues:

- **Think deeply and carefully** before implementing solutions
- **Think out loud or use a scratchpad** to organize your thoughts when approaching difficult problems
- Break down complex problems into smaller, manageable steps
- Consider multiple approaches before selecting the optimal solution
- Document your reasoning for significant implementation decisions
- When debugging, use systematic hypothesis testing rather than random changes