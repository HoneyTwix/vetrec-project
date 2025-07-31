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
- **CRITICAL: Only extract items that are explicitly mentioned or clearly implied in the CURRENT transcript. Do not invent information or copy data from example cases.**
- **CRITICAL: The transcript data is the SOURCE OF TRUTH. Example cases and previous visits are only for structural guidance.**
- Use the previous visit context if provided to maintain continuity in care, but prioritize current transcript data.
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

**CRITICAL DATA PRIORITY RULE:**
The transcript data ALWAYS takes precedence over any example cases or previous visits. Use the example cases and previous visits ONLY as structural guidelines and formatting examples. 

**DO NOT** copy specific data (dates, times, medications, dosages, etc.) from example cases or previous visits unless that exact same information appears in the current transcript.

**Examples of what NOT to do:**
- If an example case shows "due in 3 weeks" but the transcript says "due in 2 weeks", use "2 weeks" from the transcript
- If an example case shows "metformin 1000mg" but the transcript says "metformin 500mg", use "500mg" from the transcript  
- If an example case shows "high priority" but the transcript doesn't specify priority, don't assume "high priority"

**Examples of what TO do:**
- Use example cases to understand the structure and format of the data
- Use example cases to understand what types of information to look for
- Use example cases to understand how to categorize different types of tasks
- Extract ONLY the specific information mentioned in the current transcript

**Use the relevant example cases and previous visits provided in the context to guide your extraction STRUCTURE and FORMAT, but extract ONLY the specific data from the current transcript.**

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

function ExtractMedicalActionsZeroShot(
  transcript: string,
  notes: string?,
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
- **CRITICAL: Only extract items that are explicitly mentioned or clearly implied in the CURRENT transcript. Do not invent information or copy data from example cases.**
- **CRITICAL: The transcript data is the SOURCE OF TRUTH. Example cases and previous visits are only for structural guidance.**
- Use the previous visit context if provided to maintain continuity in care, but prioritize current transcript data.
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

**CRITICAL DATA PRIORITY RULE:**
The transcript data ALWAYS takes precedence over any example cases or previous visits. Use the example cases and previous visits ONLY as structural guidelines and formatting examples. 

**DO NOT** copy specific data (dates, times, medications, dosages, etc.) from example cases or previous visits unless that exact same information appears in the current transcript.

**Examples of what NOT to do:**
- If an example case shows "due in 3 weeks" but the transcript says "due in 2 weeks", use "2 weeks" from the transcript
- If an example case shows "metformin 1000mg" but the transcript says "metformin 500mg", use "500mg" from the transcript  
- If an example case shows "high priority" but the transcript doesn't specify priority, don't assume "high priority"

**Examples of what TO do:**
- Use example cases to understand the structure and format of the data
- Use example cases to understand what types of information to look for
- Use example cases to understand how to categorize different types of tasks
- Extract ONLY the specific information mentioned in the current transcript

**Use the relevant example cases and previous visits provided in the context to guide your extraction STRUCTURE and FORMAT, but extract ONLY the specific data from the current transcript.**

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

// Function to refine and improve medical extractions
function RefineMedicalExtraction(
  original_extraction: MedicalExtraction,
  transcript: string,
  confidence_level: "high" | "medium" | "low",
  notes: string?,
  previous_visits: string?,
  sops: SOP[]?
) -> MedicalExtraction {
  client "openai/gpt-4o"
  prompt #"
You are a medical extraction refinement specialist. Your task is to review, improve, and enhance a medical extraction to ensure it is accurate, complete, and actionable.

{% if sops %}
**CLINIC POLICIES AND PROCEDURES:**
The following Standard Operating Procedures (SOPs) should guide your refinement:

{% for sop in sops %}
**{{ sop.title }}** (Priority: {{ sop.priority }})
{% if sop.description %}{{ sop.description }}{% endif %}
{% if sop.category %}Category: {{ sop.category }}{% endif %}

{{ sop.content }}

---
{% endfor %}
{% endif %}

**REFINEMENT OBJECTIVES:**

1. **ACCURACY CHECK**: Verify all extracted information matches the original transcript exactly
2. **COMPLETENESS**: Identify any missing actionable items that should be extracted
3. **CONSISTENCY**: Ensure logical consistency across all extraction categories
4. **MEDICAL VALIDATION**: Validate medical terminology, dosages, and procedures
5. **STRUCTURAL IMPROVEMENT**: Improve descriptions, formatting, and categorization
6. **PRIORITY OPTIMIZATION**: Ensure appropriate priority levels based on medical urgency

**REFINEMENT GUIDELINES:**

**Follow-up Tasks:**
- Ensure descriptions are specific and actionable
- Verify priority levels match medical urgency
- Check that due dates are realistic and properly formatted
- Confirm proper assignment (client/clinician/both)
- Remove any duplicate or redundant tasks

**Medication Instructions:**
- Validate medication names and dosages
- Ensure frequency and duration are clearly specified
- Check for any missing special instructions
- Verify medical accuracy of prescriptions
- Standardize medication terminology

**Client Reminders:**
- Ensure reminder types are appropriate
- Verify descriptions are clear and actionable
- Check priority levels match importance
- Confirm due dates are realistic
- Remove any vague or non-actionable reminders

**Clinician To-Dos:**
- Verify task types are correctly categorized
- Ensure descriptions are specific and actionable
- Check priority levels match urgency
- Confirm proper assignment
- Validate medical procedures and referrals

**Custom Extractions:**
- Review for accuracy and completeness
- Ensure proper categorization
- Validate extracted data against transcript
- Improve reasoning if provided

**QUALITY IMPROVEMENTS:**

1. **Specificity**: Make descriptions more specific and actionable
2. **Consistency**: Ensure consistent terminology and formatting
3. **Completeness**: Add any missing but implied information
4. **Medical Accuracy**: Validate against medical best practices
5. **Clarity**: Improve readability and understanding

**CONFIDENCE-BASED REFINEMENT:**

- **High Confidence**: Focus on minor improvements and consistency
- **Medium Confidence**: More thorough review and enhancement
- **Low Confidence**: Comprehensive review with potential restructuring

**CRITICAL RULES:**

1. **NEVER invent information not present in the transcript**
2. **ALWAYS maintain the original intent and meaning**
3. **PRESERVE all original data unless clearly incorrect**
4. **IMPROVE formatting and clarity without changing substance**
5. **VALIDATE against medical best practices when possible**

**ORIGINAL TRANSCRIPT:**
{{ transcript }}

{% if notes %}
**ADDITIONAL NOTES:**
{{ notes }}
{% endif %}

{% if previous_visits %}
**PREVIOUS VISITS CONTEXT:**
{{ previous_visits }}
{% endif %}

**ORIGINAL EXTRACTION TO REFINE:**
{{ original_extraction }}

**CONFIDENCE LEVEL:** {{ confidence_level }}

Please review and refine this extraction to improve its quality, accuracy, and completeness while maintaining all original information and intent.

{{ ctx.output_format }}
"#
} 