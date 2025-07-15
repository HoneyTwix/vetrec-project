# Assessment: LLM-Powered Medical Visit Action Extraction System

## Objective

Build a system using BAML and LLMs that processes a medical consult transcript and notes, then extracts:

- Reminders
- Action items
- To-dos

Use Python with FastAPI for backend if needed, BAML for all prompting logic, and React for frontend
implementation.

Evaluation is based on LLM prompt design, reasoning, BAML usage, code quality, and ability to iterate.

## Section 1: Prompt Design + BAML Task Setup

Goal: Create a BAML task that uses an LLM to extract:

- Follow-up tasks
- Medication instructions
- Client-facing reminders
- Clinician to-dos

Deliverables:

- Prompt template for the LLM
- Sample input/output using fictional transcript/notes
- .baml task definition (include input/output schema, model config, and logic)

## Section 2: System Integration

Goal: Set up a FastAPI endpoint or script that:

- Accepts transcript + notes as input
- Invokes the BAML task
- Returns structured JSON of extractions

Deliverables:

- Python code using FastAPI and BAML SDK


# Assessment: LLM-Powered Medical Visit Action Extraction System

- Sample request and response

## Section 3: Evaluation + Iteration

Goal: Add logic to evaluate LLM output quality against gold-standard samples.

Deliverables:

- Script for comparison
- Defined metrics (e.g. overlap, precision, recall)

## Section 4: UI for E2E Testing

Goal: Build a simple React frontend to:

- Input or upload transcript + notes
- Display extracted reminders, action items, and to-dos
- Visualize or export structured output

Deliverables:

- Functional UI in React
- Working end-to-end connection with FastAPI + BAML backend

## Stretch Goal

- Allow users to define custom extraction categories (e.g. "Billing follow-up", "Diagnostic reminder")
- Support loading SOPs or clinic policies into the LLM context dynamically


