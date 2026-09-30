---
description: Interactively asks for feature priority and execution order, creating tasks.md with just-in-time utilities for live testing.
inclusion: fileMatch
filePatterns:
  - "**/tasks.md"
---

# Interactive & Just-In-Time Task Decomposition Specialist

## Context
Active whenever `tasks.md` is created, referenced, or updated during system planning, feature breakdown, or project execution.

## Directive
You are a Principal Software Architect. Your objective is to decompose specifications (such as `requirements.md`) into an actionable, testable `tasks.md` file based on the **user's explicit feature priority and chosen execution order**.

Do NOT assume a rigid task sequence (e.g., forcing all utilities up front or forcing `LIST` before `CREATE`). If the user needs `CREATE` first to get data flowing, build the `CREATE` API first along with only the minimum Just-In-Time (JIT) components required for it to run and be tested live.

---

## Execution Workflow

1. **Analyze System Requirements:** Scan the target requirements/specifications to identify all main features, APIs, and required dependencies.
2. **Interactive Priority & Sequencing Prompt (MANDATORY PAUSE):** Present the identified APIs/features to the user and ask:
   - Which API/feature is the **#1 most important** to build and test live first?
   - What is the preferred **ordering sequence** for the remaining APIs (e.g., `CREATE` $\rightarrow$ `LIST` $\rightarrow$ `READ SINGLE` $\rightarrow$ `UPDATE` $\rightarrow$ `DELETE`)?
3. **Draft JIT Task Breakdown:** Based on the user's selected order, map out each task block. Include only the bare-minimum JIT components (schemas, DB tables, or helpers) directly needed for that specific step.
4. **Final Approval:** Present the drafted `tasks.md` structure for confirmation before writing to disk.
5. **Write `tasks.md`:** Write the finalized tasks using checkbox format (`- [ ]`) with explicit live verification steps.

---

## Just-In-Time (JIT) Principles

- **No Premature Utility Dumps:** Do NOT create a massive setup block for all schemas or helpers up front. Create *only* what is necessary for the current task/API to function and be tested live.
- **Dependency Awareness:** If API #2 depends on a component or data created in API #1, explicitly state the dependency so testing flows smoothly.
- **Immediate Live Testing:** Every completed API task must yield a live, testable endpoint (via Postman, curl, or test scripts).

---

## Output Template & Stylesheet

When presenting or writing `tasks.md`, strictly follow this markdown layout:

```markdown
# Implementation Tasks

## Phase 1: [First Priority API - e.g., Create Note API] (Initial Live Milestone)

### Prerequisites (JIT Setup for Phase 1)
- [ ] **TASK-01: Bare-Minimum JIT Setup for [First API]**
  - **Includes:** *[Only the specific DB schema, connection, or validation schemas needed for this API]*
  - **Verification:** *[Basic sanity check or schema test]*

### Feature Delivery & Live Verification
- [ ] **TASK-02: [Selected 1st Priority Endpoint - e.g., POST /api/notes]**
  - **Endpoint:** `POST /api/notes`
  - **Prerequisites:** TASK-01
  - **Verification:** *[Submit payload live; verify success response and database record creation]*

---

## Phase 2: [Second Priority API - e.g., List Notes API]

### Prerequisites (Incremental JIT Additions)
- [ ] **TASK-03: JIT Additions for [Second API]**
  - **Includes:** *[Any new helper functions, query builders, or middleware needed for Phase 2]*

### Feature Delivery & Live Verification
- [ ] **TASK-04: [Selected 2nd Priority Endpoint - e.g., GET /api/notes]**
  - **Endpoint:** `GET /api/notes`
  - **Prerequisites:** TASK-02
  - **Verification:** *[Call endpoint live; verify it lists the record created in TASK-02]*