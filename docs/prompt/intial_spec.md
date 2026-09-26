Act as a Principal FastAPI Software Architect. Implement [INSERT TASK NUMBER AND TASK NAME HERE] following the system design and strict quality rules.

### Requirements & Constraints:
1. **Bridge File Format**: Output all generated code files using the exact standard delimiter:
--------app-bridge-----------
<relative_file_path>
<code_content>
--------app-bridge-----------

2. **Strict Docstring Standards**: Every Python file and function/method MUST include a docstring adhering strictly to these four sections only (no extra fluff, code examples, or author lines):
   - **Purpose**: A concise summary of what the file/function does.
   - **Flow**: High-level execution steps or logical pipeline (numbered steps).
   - **Inputs**: Explanation of parameters (omit if no parameters).
   - **Outputs**: Explanation of return values or output behavior.

3. **Layered Architecture**: Follow clear separation of concerns (Endpoints -> Schemas -> Services -> Repositories -> Models/Storage).

4. **Documentation Artifact**: End the output by generating or updating the documentation file `docs/spec/initial/task_[TASK_NUMBER].md` containing:
   - Simple explanations of the purpose and code of each file created in this task.
   - A brief summary recap of earlier tasks.