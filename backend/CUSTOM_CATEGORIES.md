# Custom Extraction Categories

This feature allows users to define custom extraction categories beyond the standard medical extraction fields. Users can specify custom categories in their API requests to extract domain-specific information.

## Overview

Custom categories enable flexible extraction of specialized information such as:
- Billing follow-up tasks
- Diagnostic reminders
- Pharmacy coordination
- Insurance coverage details
- Compliance requirements
- Administrative tasks

## Usage

### Request Format

Add a `custom_categories` array to your extraction request:

```json
{
  "transcript_text": "Doctor: Patient presents with chest pain...",
  "notes": "",
  "user_id": 123,
  "custom_categories": [
    {
      "name": "billing_follow_up",
      "description": "Extract any billing-related tasks or follow-ups mentioned",
      "field_type": "structured",
      "required_fields": ["task_description", "department", "priority"],
      "optional_fields": ["due_date", "notes"]
    }
  ]
}
```

### Field Types

#### 1. Text (`"text"`)
Extract simple text information:
```json
{
  "name": "pharmacy_notes",
  "description": "Extract pharmacy-related notes",
  "field_type": "text",
  "required_fields": ["notes"],
  "optional_fields": ["priority"]
}
```

#### 2. List (`"list"`)
Extract arrays of items:
```json
{
  "name": "diagnostic_tests",
  "description": "Extract diagnostic tests and monitoring requirements",
  "field_type": "list",
  "required_fields": ["test_name", "frequency", "due_date"],
  "optional_fields": ["special_instructions", "priority"]
}
```

#### 3. Structured (`"structured"`)
Extract structured data with specific fields:
```json
{
  "name": "insurance_coverage",
  "description": "Extract insurance and coverage-related information",
  "field_type": "structured",
  "required_fields": ["coverage_type", "action_needed"],
  "optional_fields": ["contact_person", "due_date"]
}
```

## Response Format

Custom extractions are included in the response under `custom_extractions`:

```json
{
  "transcript": { ... },
  "extraction": {
    "id": 1,
    "transcript_id": 1,
    "follow_up_tasks": [ ... ],
    "medication_instructions": [ ... ],
    "client_reminders": [ ... ],
    "clinician_todos": [ ... ],
    "custom_extractions": {
      "billing_follow_up": {
        "extracted_data": "Follow up with billing department about insurance coverage for cardiac stress test",
        "confidence": "high",
        "reasoning": "Explicitly mentioned billing department and insurance coverage"
      }
    },
    "evaluation_results": { ... },
    "created_at": "2025-07-14T..."
  }
}
```

## Examples

### Example 1: Billing Follow-up
```json
{
  "transcript_text": "Doctor: Patient presents with chest pain. I'm ordering an EKG and blood work. Also, please follow up with billing department about the patient's insurance coverage for the cardiac stress test we discussed.",
  "custom_categories": [
    {
      "name": "billing_follow_up",
      "description": "Extract any billing-related tasks or follow-ups mentioned",
      "field_type": "structured",
      "required_fields": ["task_description", "department", "priority"],
      "optional_fields": ["due_date", "notes"]
    }
  ]
}
```

### Example 2: Diagnostic Reminders
```json
{
  "transcript_text": "Doctor: Patient has diabetes and needs regular monitoring. Schedule HbA1c test for next month, and remind patient to check blood sugar daily.",
  "custom_categories": [
    {
      "name": "diagnostic_reminders",
      "description": "Extract diagnostic tests and monitoring requirements",
      "field_type": "list",
      "required_fields": ["test_name", "frequency", "due_date"],
      "optional_fields": ["special_instructions", "priority"]
    }
  ]
}
```

### Example 3: Multiple Categories
```json
{
  "transcript_text": "Doctor: Patient with hypertension needs medication adjustment. Also, please contact the pharmacy about prescription coverage.",
  "custom_categories": [
    {
      "name": "pharmacy_coordination",
      "description": "Extract pharmacy-related tasks and coordination",
      "field_type": "text",
      "required_fields": ["task_description"],
      "optional_fields": ["pharmacy_name", "priority"]
    },
    {
      "name": "insurance_coverage",
      "description": "Extract insurance and coverage-related information",
      "field_type": "structured",
      "required_fields": ["coverage_type", "action_needed"],
      "optional_fields": ["contact_person", "due_date"]
    }
  ]
}
```

## Testing

Run the test script to see custom categories in action:

```bash
python test_custom_categories.py
```

## Migration

If you have an existing database, run the migration script:

```bash
python utils/migrate_custom_extractions.py
```

## Benefits

1. **Flexibility**: Extract domain-specific information beyond standard medical fields
2. **Customization**: Define categories that match your workflow needs
3. **Structured Data**: Get organized, structured output for custom categories
4. **Confidence Scoring**: Each custom extraction includes confidence and reasoning
5. **Integration**: Custom extractions work with the existing evaluation system

## Limitations

- Custom categories are extracted only when explicitly mentioned in the transcript
- The AI will not invent information not present in the transcript
- Field types and validation are enforced by the extraction logic
- Custom extractions are stored as JSON and may not be searchable via embeddings 