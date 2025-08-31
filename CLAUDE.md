# Development Partnership

We build production code together. I handle implementation details while you guide architecture and catch complexity early.

## Core Workflow: Research → Plan → Implement → Validate

**Start every feature with:** "Let me research the codebase and create a plan before implementing."

1. **Research** - Understand existing patterns and architecture
2. **Plan** - Propose approach and verify with you
3. **Implement** - Build with tests and error handling
4. **Validate** - ALWAYS run formatters, linters, and tests after implementation

## Code Organization

**Keep functions small and focused:**

- If you need comments to explain sections, split into functions
- Group related functionality into clear packages
- Prefer many small files over few large ones

## Bash commands

- source .venv/bin/activate: Activate Python virtual environment
- just test: Run tests

## Application context

We develop a Python library for optimizing a multi-energy system. A user can create a custom energy system by defining assets (PowerGenerator, Battery, etc.) toguether coupled with conditions such as a fixed load.
An energy sytem can then be optimized to minimize costs
