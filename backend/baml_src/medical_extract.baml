// Medical extraction types
class FollowUpTask {
  description string
  priority "high" | "medium" | "low"
  due_date string?
  assigned_to "client" | "clinician" | "both"?
}

class MedicationInstruction {
  medication_name string
  dosage string
  frequency string
  duration string
  special_instructions string?
}

class ClientReminder {
  reminder_type "appointment" | "medication" | "test" | "lifestyle" | "other"
  description string
  due_date string?
  priority "high" | "medium" | "low"
}

class ClinicianTodo {
  task_type "follow_up" | "referral" | "test_order" | "documentation" | "billing" | "other"
  description string
  priority "high" | "medium" | "low"
  assigned_to string?
  due_date string?
}

class CustomCategory {
  name string
  description string
  field_type "text" | "list" | "structured"
  required_fields string[]?
  optional_fields string[]?
}

class CustomExtraction {
  category_name string
  extracted_data string
  confidence "high" | "medium" | "low"
  reasoning string?
}

class SOP {
  title string
  description string?
  content string
  category string?
  priority int
}

class MedicalExtraction {
  follow_up_tasks FollowUpTask[]
  medication_instructions MedicationInstruction[]
  client_reminders ClientReminder[]
  clinician_todos ClinicianTodo[]
  custom_extractions CustomExtraction[]?
}

// Function to extract medical actions from transcripts
function ExtractMedicalActions(
  transcript: string,
  notes: string?,
  previous_visits: string?,
  custom_categories: CustomCategory[]?,
  sops: SOP[]?
) -> MedicalExtraction {
  client "openai/gpt-4o"
  prompt #"
You are a medical assistant tasked with extracting actionable items from medical visit transcripts.

{% if sops %}
**CLINIC POLICIES AND PROCEDURES:**
The following Standard Operating Procedures (SOPs) and clinic policies should guide your extraction:

{% for sop in sops %}
**{{ sop.title }}** (Priority: {{ sop.priority }})
{% if sop.description %}{{ sop.description }}{% endif %}
{% if sop.category %}Category: {{ sop.category }}{% endif %}

{{ sop.content }}

---
{% endfor %}

**IMPORTANT:** Use these SOPs to ensure your extraction follows clinic-specific protocols, procedures, and requirements. Pay special attention to:
- Required documentation standards
- Specific referral procedures
- Medication protocols
- Follow-up scheduling requirements
- Billing and coding requirements
- Quality assurance measures
{% endif %}

Extract and return the following as separate lists (empty if none):

1. **Follow-up Tasks**: All actions that need to be completed after the visit, including scheduling, monitoring, or returning for follow-up. For each, include:
   - description (be specific, e.g., "Schedule blood work for tomorrow", "Monitor blood sugar daily")
   - priority ("high", "medium", "low")
   - due_date (if mentioned)
   - assigned_to ("client", "clinician", or "both")
   - **Include all scheduling actions (e.g., "Schedule podiatry referral") and assign to "clinician" if performed by staff.**

2. **Medication Instructions**: All medications prescribed or discussed, with:
   - medication_name
   - dosage
   - frequency
   - duration
   - special_instructions (if any)

3. **Client Reminders**: Any reminders for the patient, such as appointments, tests, or lifestyle changes. For each, include:
   - reminder_type ("appointment", "medication", "test", "lifestyle", "other")
   - description (be specific, e.g., "Blood work appointment tomorrow", "Monitor blood sugar daily")
   - due_date (if mentioned)
   - priority

4. **Clinician To-Dos**: Any tasks for the clinician or staff, such as referrals, test orders, documentation, or scheduling. For each, include:
   - task_type ("follow_up", "referral", "test_order", "documentation", "billing", "other")
   - description (be specific)
   - priority
   - assigned_to (if mentioned)
   - due_date (if mentioned)
   - **Include all scheduling actions and referrals here as well.**

{% if custom_categories %}
5. **Custom Categories**: Extract information for the following custom categories:
{% for category in custom_categories %}
   - **{{ category.name }}**: {{ category.description }}
     - Field type: {{ category.field_type }}
     {% if category.required_fields %}
     - Required fields: {{ category.required_fields | join(", ") }}
     {% endif %}
     {% if category.optional_fields %}
     - Optional fields: {{ category.optional_fields | join(", ") }}
     {% endif %}
{% endfor %}

For each custom category, extract relevant information based on the field type:
- **text**: Extract as simple text
- **list**: Extract as an array of items
- **structured**: Extract as structured data with the specified fields
{% endif %}

**Instructions:**
- If an action is mentioned by a nurse or staff, assign to "clinician".
- If a patient is to do something, assign to "client".
- If an action fits multiple categories, include it in all relevant categories.
- Be specific in descriptions; avoid vague terms like "Podiatry referral"—prefer "Schedule podiatry referral".    
- Only extract items that are explicitly mentioned or clearly implied. Do not invent information.
- Use the previous visit context if provided to maintain continuity in care.
- Format all dates as YYYY-MM-DD or relative dates (e.g., "in 2 weeks", "next month").
- For custom categories, extract only information that is explicitly mentioned in the transcript.
{% if sops %}
- **CRITICAL**: Follow the clinic SOPs and policies provided above. Ensure all extractions comply with clinic-specific procedures, documentation requirements, and protocols.
- If SOPs specify particular formats, requirements, or procedures, incorporate these into your extraction.
- Use SOPs to determine appropriate task assignments, priorities, and follow-up procedures.
{% endif %}

**Examples:**

Follow-up Tasks:
- description: "Schedule blood work for tomorrow"
  priority: "high"
  due_date: "tomorrow"
  assigned_to: "clinician"
- description: "Return for follow-up in 1 month"
  priority: "medium"
  due_date: "in 1 month"
  assigned_to: "client"
- description: "Monitor blood sugar daily"
  priority: "high"
  due_date: "ongoing"
  assigned_to: "client"

Medication Instructions:
- medication_name: "metformin"
  dosage: "500mg"
  frequency: "twice daily"
  duration: "ongoing"
  special_instructions: "for diabetes"

Client Reminders:
- reminder_type: "test"
  description: "Blood work appointment tomorrow"
  due_date: "tomorrow"
  priority: "high"
- reminder_type: "lifestyle"
  description: "Monitor blood sugar daily"
  due_date: "ongoing"
  priority: "high"
- reminder_type: "appointment"
  description: "Follow-up appointment in 1 month"
  due_date: "in 1 month"
  priority: "medium"

Clinician To-Dos:
- task_type: "test_order"
  description: "Order blood work including HbA1c"
  priority: "high"
  assigned_to: "clinician"
  due_date: "tomorrow"
- task_type: "referral"
  description: "Refer to podiatry for foot pain"
  priority: "medium"
  assigned_to: "clinician"
  due_date: "asap"
- task_type: "follow_up"
  description: "Schedule follow-up appointment in 1 month"
  priority: "medium"
  due_date: "in 1 month"

{% if custom_categories %}
Custom Categories Examples:
{% for category in custom_categories %}
- **{{ category.name }}**: Extract relevant information based on the description and field type
{% endfor %}
{% endif %}

---

**Use the relevant example cases and previous visits provided in the context to guide your extraction.**

{% if sops %}
**CRITICAL REMINDER:** Ensure all extractions comply with the clinic SOPs and policies provided above. These policies take precedence over general medical practices and should guide your extraction decisions.
{% endif %}

---

**Negative Example (do NOT extract):**
- Do not extract vague statements like "Patient discussed diabetes" unless there is an actionable item.
- Do not invent tasks or reminders not present in the transcript.
- For custom categories, only extract information explicitly mentioned in the transcript.

Please extract actionable items from the following medical visit transcript:

TRANSCRIPT:
{{ transcript }}

{% if notes %}
ADDITIONAL NOTES:
{{ notes }}
{% endif %}

{% if previous_visits %}
PREVIOUS VISITS CONTEXT:
{{ previous_visits }}
{% endif %}

{% if custom_categories %}
CUSTOM CATEGORIES TO EXTRACT:
{% for category in custom_categories %}
- {{ category.name }}: {{ category.description }} ({{ category.field_type }})
{% endfor %}
{% endif %}

{{ ctx.output_format }}
"#
}

// Test the function with a sample medical transcript
test sample_medical_transcript {
  functions [ExtractMedicalActions]
  args {
    transcript #"
      Doctor: Mrs. Johnson, I see your blood pressure is still elevated at 160/95. 
      I want you to return in 2 weeks for a follow-up to check your blood pressure. 
      If it's still elevated, we might need to adjust your medication. 
      Also, please make sure to take your lisinopril 10mg once daily at the same time each day.
      I'll also order some blood work to check your kidney function.
    "#
    notes "Patient has history of high blood pressure"
  }
} 