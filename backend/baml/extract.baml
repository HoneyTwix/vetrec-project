class ExtractMedicalActions {
  doc "Extract actionable items from medical visit transcripts"
  
  input {
    transcript: string
    notes?: string
    previous_visits?: string
  }
  
  output {
    follow_up_tasks: {
      description: string
      priority: "high" | "medium" | "low"
      due_date?: string
      assigned_to?: "client" | "clinician" | "both"
    }[]
    medication_instructions: {
      medication_name: string
      dosage: string
      frequency: string
      duration: string
      special_instructions?: string
    }[]
    client_reminders: {
      reminder_type: "appointment" | "medication" | "test" | "lifestyle" | "other"
      description: string
      due_date?: string
      priority: "high" | "medium" | "low"
    }[]
    clinician_todos: {
      task_type: "follow_up" | "referral" | "test_order" | "documentation" | "billing" | "other"
      description: string
      priority: "high" | "medium" | "low"
      assigned_to?: string
      due_date?: string
    }[]
  }
  
  prompt {
    system: |
      You are a medical assistant tasked with extracting actionable items from medical visit transcripts. 
      Your role is to identify and categorize:
      
      1. Follow-up tasks that need to be completed
      2. Medication instructions for patients
      3. Client-facing reminders and appointments
      4. Clinician to-dos and administrative tasks
      
      Be thorough but concise. Only extract items that are explicitly mentioned or clearly implied.
      Use the previous visit context if provided to maintain continuity in care.
      
      Format all dates as YYYY-MM-DD or relative dates (e.g., "in 2 weeks", "next month").
      
    user: |
      Please extract actionable items from the following medical visit transcript:
      
      TRANSCRIPT:
      {{transcript}}
      
      {{#if notes}}
      ADDITIONAL NOTES:
      {{notes}}
      {{/if}}
      
      {{#if previous_visits}}
      PREVIOUS VISITS CONTEXT:
      {{previous_visits}}
      {{/if}}
      
      Please provide a structured extraction of:
      - Follow-up tasks with priority levels
      - Medication instructions with dosages and schedules
      - Client reminders for appointments, tests, or lifestyle changes
      - Clinician to-dos for administrative tasks, referrals, or documentation
  }
  
  client baml {
    provider baml-openai-chat
    model gpt-4
    temperature 0.1
  }
}
