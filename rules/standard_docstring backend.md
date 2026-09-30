# Strict Docstring Standards

Enforce focused docstrings covering purpose, flow, inputs, and outputs for all code generated or modified in this workspace.

## Core Directives

1. **Mandatory Docstrings**: Every source code file and every function/method must include a docstring.
2. **Strict Scope**: Docstrings MUST ONLY contain the following four sections:
   - **Purpose**: A concise summary of what the file or function does.
   - **Flow**: High-level execution steps or logical pipeline (sequence of operations).
   - **Inputs**: Clear explanation of parameters/inputs (omit if function accepts no arguments).
   - **Outputs**: Clear explanation of return value(s) or output behavior.
3. **No Fluff**: Do NOT include code examples, author names, changelogs, type annotations inside text (use native language type hints instead), or external links.

## Templates & Examples

### File-Level Header
Place at the top of every file:

```python
"""
Purpose: Coordinates user authentication and session management.
Flow: 
      1. Check stock availability for all items.
      2. Charge payment source.
      3. Decrement inventory level.
      4. Trigger shipping notification.
Inputs: Configuration settings from application context and HTTP request headers.
Outputs: Exposes auth middleware and session verification handles.
"""