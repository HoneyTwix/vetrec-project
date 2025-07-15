"""
Sample test cases for evaluating extraction quality
"""

SAMPLE_TEST_CASES = [
    {
        "name": "Basic medication prescription",
        "transcript": """
        Doctor: Patient presents with mild hypertension. I'm prescribing lisinopril 10mg 
        once daily for 30 days. Please schedule a follow-up in 2 weeks to monitor blood pressure.
        """,
        "gold_standard": {
            "follow_up_tasks": [
                {
                    "description": "Schedule follow-up appointment in 2 weeks",
                    "priority": "high",
                    "due_date": "in 2 weeks",
                    "assigned_to": "clinician"
                }
            ],
            "medication_instructions": [
                {
                    "medication_name": "lisinopril",
                    "dosage": "10mg",
                    "frequency": "once daily",
                    "duration": "30 days",
                    "special_instructions": "for hypertension"
                }
            ],
            "client_reminders": [
                {
                    "reminder_type": "appointment",
                    "description": "Follow-up appointment in 2 weeks",
                    "due_date": "in 2 weeks",
                    "priority": "high"
                }
            ],
            "clinician_todos": [
                {
                    "task_type": "follow_up",
                    "description": "Schedule follow-up appointment for blood pressure monitoring",
                    "priority": "high",
                    "due_date": "in 2 weeks"
                }
            ]
        }
    },
    {
        "name": "Complex case with multiple actions",
        "transcript": """
        Doctor: Patient has diabetes and reports foot pain. I'm ordering blood work 
        including HbA1c, and referring to podiatry. Also prescribing metformin 500mg 
        twice daily. Patient needs to monitor blood sugar daily and return in 1 month.
        Nurse: I'll schedule the blood work for tomorrow and the podiatry referral.
        """,
        "gold_standard": {
            "follow_up_tasks": [
                {
                    "description": "Schedule blood work for tomorrow",
                    "priority": "high",
                    "due_date": "tomorrow",
                    "assigned_to": "clinician"
                },
                {
                    "description": "Schedule podiatry referral",
                    "priority": "medium",
                    "due_date": "asap",
                    "assigned_to": "clinician"
                },
                {
                    "description": "Return for follow-up in 1 month",
                    "priority": "medium",
                    "due_date": "in 1 month",
                    "assigned_to": "client"
                }
            ],
            "medication_instructions": [
                {
                    "medication_name": "metformin",
                    "dosage": "500mg",
                    "frequency": "twice daily",
                    "duration": "ongoing",
                    "special_instructions": "for diabetes"
                }
            ],
            "client_reminders": [
                {
                    "reminder_type": "test",
                    "description": "Blood work appointment tomorrow",
                    "due_date": "tomorrow",
                    "priority": "high"
                },
                {
                    "reminder_type": "lifestyle",
                    "description": "Monitor blood sugar daily",
                    "due_date": "ongoing",
                    "priority": "high"
                },
                {
                    "reminder_type": "appointment",
                    "description": "Follow-up appointment in 1 month",
                    "due_date": "in 1 month",
                    "priority": "medium"
                }
            ],
            "clinician_todos": [
                {
                    "task_type": "test_order",
                    "description": "Order blood work including HbA1c",
                    "priority": "high",
                    "due_date": "tomorrow"
                },
                {
                    "task_type": "referral",
                    "description": "Refer to podiatry for foot pain",
                    "priority": "medium",
                    "due_date": "asap"
                },
                {
                    "task_type": "follow_up",
                    "description": "Schedule follow-up appointment in 1 month",
                    "priority": "medium",
                    "due_date": "in 1 month"
                }
            ]
        }
    },
    {
        "name": "Emergency case",
        "transcript": """
        Doctor: Patient presents with chest pain and shortness of breath. 
        EKG shows ST elevation. Immediate transfer to emergency room required.
        Nurse: I'll call 911 and prepare transfer paperwork.
        """,
        "gold_standard": {
            "follow_up_tasks": [
                {
                    "description": "Immediate transfer to emergency room",
                    "priority": "high",
                    "due_date": "immediate",
                    "assigned_to": "clinician"
                },
                {
                    "description": "Call 911 for emergency transfer",
                    "priority": "high",
                    "due_date": "immediate",
                    "assigned_to": "clinician"
                }
            ],
            "medication_instructions": [],
            "client_reminders": [
                {
                    "reminder_type": "other",
                    "description": "Emergency transfer to hospital",
                    "due_date": "immediate",
                    "priority": "high"
                }
            ],
            "clinician_todos": [
                {
                    "task_type": "documentation",
                    "description": "Prepare transfer paperwork",
                    "priority": "high",
                    "due_date": "immediate"
                },
                {
                    "task_type": "follow_up",
                    "description": "Follow up on emergency transfer outcome",
                    "priority": "high",
                    "due_date": "asap"
                }
            ]
        }
    },
    {
        "name": "Simple annual physical",
        "transcript": """
        Doctor: Patient here for annual physical. All vitals are normal. 
        Schedule next year's annual physical appointment.
        """,
        "gold_standard": {
            "follow_up_tasks": [
                {
                    "description": "Schedule next year's annual physical",
                    "priority": "medium",
                    "due_date": "next year",
                    "assigned_to": "clinician"
                }
            ],
            "medication_instructions": [],
            "client_reminders": [
                {
                    "reminder_type": "appointment",
                    "description": "Annual physical completed",
                    "due_date": "completed",
                    "priority": "medium"
                }
            ],
            "clinician_todos": [
                {
                    "task_type": "documentation",
                    "description": "Document annual physical findings",
                    "priority": "medium",
                    "due_date": "today"
                }
            ]
        }
    },
    {
        "name": "Medium complexity - Depression management",
        "transcript": """
        Doctor: Patient reports symptoms of depression. Prescribing sertraline 50mg 
        once daily and referring to psychotherapy. Patient should monitor mood changes 
        and report any suicidal thoughts immediately. Schedule follow-up in 4 weeks 
        to assess medication effectiveness. Also order thyroid function tests to rule 
        out underlying cause.
        """,
        "gold_standard": {
            "follow_up_tasks": [
                {
                    "description": "Schedule follow-up in 4 weeks",
                    "priority": "high",
                    "due_date": "in 4 weeks",
                    "assigned_to": "clinician"
                },
                {
                    "description": "Order thyroid function tests",
                    "priority": "medium",
                    "due_date": "asap",
                    "assigned_to": "clinician"
                }
            ],
            "medication_instructions": [
                {
                    "medication_name": "sertraline",
                    "dosage": "50mg",
                    "frequency": "once daily",
                    "duration": "ongoing",
                    "special_instructions": "for depression"
                }
            ],
            "client_reminders": [
                {
                    "reminder_type": "lifestyle",
                    "description": "Monitor mood changes",
                    "due_date": "ongoing",
                    "priority": "high"
                },
                {
                    "reminder_type": "appointment",
                    "description": "Follow-up appointment in 4 weeks",
                    "due_date": "in 4 weeks",
                    "priority": "high"
                }
            ],
            "clinician_todos": [
                {
                    "task_type": "referral",
                    "description": "Refer to psychotherapy",
                    "priority": "high",
                    "due_date": "asap"
                },
                {
                    "task_type": "test_order",
                    "description": "Order thyroid function tests",
                    "priority": "medium",
                    "due_date": "asap"
                },
                {
                    "task_type": "follow_up",
                    "description": "Schedule follow-up for medication assessment",
                    "priority": "high",
                    "due_date": "in 4 weeks"
                }
            ]
        }
    },
    {
        "name": "Complex case - Post-surgery recovery",
        "transcript": """
        Doctor: Patient recovering from hip replacement surgery. Prescribing oxycodone 
        5mg every 6 hours for pain, aspirin 81mg daily for blood clot prevention, 
        and physical therapy referral. Patient needs to monitor incision site daily, 
        avoid certain movements, and attend physical therapy 3 times per week. 
        Schedule wound check in 1 week, physical therapy evaluation in 2 weeks, 
        and follow-up with orthopedic surgeon in 1 month. Nurse: I'll coordinate 
        with physical therapy department and schedule all appointments.
        """,
        "gold_standard": {
            "follow_up_tasks": [
                {
                    "description": "Schedule wound check in 1 week",
                    "priority": "high",
                    "due_date": "in 1 week",
                    "assigned_to": "clinician"
                },
                {
                    "description": "Schedule physical therapy evaluation in 2 weeks",
                    "priority": "high",
                    "due_date": "in 2 weeks",
                    "assigned_to": "clinician"
                },
                {
                    "description": "Schedule orthopedic follow-up in 1 month",
                    "priority": "high",
                    "due_date": "in 1 month",
                    "assigned_to": "clinician"
                }
            ],
            "medication_instructions": [
                {
                    "medication_name": "oxycodone",
                    "dosage": "5mg",
                    "frequency": "every 6 hours",
                    "duration": "as needed",
                    "special_instructions": "for post-surgery pain"
                },
                {
                    "medication_name": "aspirin",
                    "dosage": "81mg",
                    "frequency": "daily",
                    "duration": "ongoing",
                    "special_instructions": "for blood clot prevention"
                }
            ],
            "client_reminders": [
                {
                    "reminder_type": "lifestyle",
                    "description": "Monitor incision site daily",
                    "due_date": "ongoing",
                    "priority": "high"
                },
                {
                    "reminder_type": "lifestyle",
                    "description": "Avoid certain movements",
                    "due_date": "ongoing",
                    "priority": "high"
                },
                {
                    "reminder_type": "appointment",
                    "description": "Physical therapy 3 times per week",
                    "due_date": "ongoing",
                    "priority": "high"
                },
                {
                    "reminder_type": "appointment",
                    "description": "Wound check in 1 week",
                    "due_date": "in 1 week",
                    "priority": "high"
                }
            ],
            "clinician_todos": [
                {
                    "task_type": "referral",
                    "description": "Refer to physical therapy",
                    "priority": "high",
                    "due_date": "asap"
                },
                {
                    "task_type": "follow_up",
                    "description": "Schedule wound check",
                    "priority": "high",
                    "due_date": "in 1 week"
                },
                {
                    "task_type": "follow_up",
                    "description": "Schedule orthopedic follow-up",
                    "priority": "high",
                    "due_date": "in 1 month"
                }
            ]
        }
    },
    {
        "name": "Simple case - Skin condition treatment",
        "transcript": """
        Doctor: Patient has mild eczema. Prescribing hydrocortisone 1% cream 
        twice daily for 2 weeks. Apply to affected areas only.
        """,
        "gold_standard": {
            "follow_up_tasks": [],
            "medication_instructions": [
                {
                    "medication_name": "hydrocortisone",
                    "dosage": "1% cream",
                    "frequency": "twice daily",
                    "duration": "2 weeks",
                    "special_instructions": "apply to affected areas only"
                }
            ],
            "client_reminders": [
                {
                    "reminder_type": "medication",
                    "description": "Apply hydrocortisone cream twice daily",
                    "due_date": "for 2 weeks",
                    "priority": "medium"
                }
            ],
            "clinician_todos": []
        }
    },
    {
        "name": "Complex case - Multiple chronic conditions",
        "transcript": """
        Doctor: Patient with COPD, heart failure, and diabetes presents with 
        worsening shortness of breath. Prescribing prednisone 20mg daily for 5 days, 
        increased albuterol inhaler use, and adjusting diabetes medications. 
        Ordering chest X-ray, pulmonary function tests, and cardiac stress test. 
        Patient needs to monitor oxygen levels, blood sugar, and weight daily. 
        Schedule pulmonology consultation, cardiology follow-up, and diabetes 
        education class. Return in 1 week for reassessment. Nurse: I'll coordinate 
        with all specialists and schedule comprehensive care plan.
        """,
        "gold_standard": {
            "follow_up_tasks": [
                {
                    "description": "Schedule pulmonology consultation",
                    "priority": "high",
                    "due_date": "asap",
                    "assigned_to": "clinician"
                },
                {
                    "description": "Schedule cardiology follow-up",
                    "priority": "high",
                    "due_date": "asap",
                    "assigned_to": "clinician"
                },
                {
                    "description": "Schedule diabetes education class",
                    "priority": "medium",
                    "due_date": "asap",
                    "assigned_to": "clinician"
                },
                {
                    "description": "Return in 1 week for reassessment",
                    "priority": "high",
                    "due_date": "in 1 week",
                    "assigned_to": "client"
                }
            ],
            "medication_instructions": [
                {
                    "medication_name": "prednisone",
                    "dosage": "20mg",
                    "frequency": "daily",
                    "duration": "5 days",
                    "special_instructions": "for COPD exacerbation"
                },
                {
                    "medication_name": "albuterol",
                    "dosage": "inhaler",
                    "frequency": "increased use",
                    "duration": "ongoing",
                    "special_instructions": "for COPD"
                }
            ],
            "client_reminders": [
                {
                    "reminder_type": "lifestyle",
                    "description": "Monitor oxygen levels daily",
                    "due_date": "ongoing",
                    "priority": "high"
                },
                {
                    "reminder_type": "lifestyle",
                    "description": "Monitor blood sugar daily",
                    "due_date": "ongoing",
                    "priority": "high"
                },
                {
                    "reminder_type": "lifestyle",
                    "description": "Monitor weight daily",
                    "due_date": "ongoing",
                    "priority": "high"
                },
                {
                    "reminder_type": "appointment",
                    "description": "Reassessment appointment in 1 week",
                    "due_date": "in 1 week",
                    "priority": "high"
                }
            ],
            "clinician_todos": [
                {
                    "task_type": "test_order",
                    "description": "Order chest X-ray",
                    "priority": "high",
                    "due_date": "asap"
                },
                {
                    "task_type": "test_order",
                    "description": "Order pulmonary function tests",
                    "priority": "high",
                    "due_date": "asap"
                },
                {
                    "task_type": "test_order",
                    "description": "Order cardiac stress test",
                    "priority": "high",
                    "due_date": "asap"
                },
                {
                    "task_type": "referral",
                    "description": "Refer to pulmonology",
                    "priority": "high",
                    "due_date": "asap"
                },
                {
                    "task_type": "referral",
                    "description": "Refer to cardiology",
                    "priority": "high",
                    "due_date": "asap"
                },
                {
                    "task_type": "follow_up",
                    "description": "Schedule reassessment appointment",
                    "priority": "high",
                    "due_date": "in 1 week"
                }
            ]
        }
    }
]

def get_test_cases():
    """Return the sample test cases"""
    return SAMPLE_TEST_CASES

def run_evaluation_on_samples():
    """Run evaluation on sample test cases"""
    from metrics import generate_evaluation_report
    
    # This would be populated with actual LLM predictions
    test_cases_with_predictions = []
    
    for test_case in SAMPLE_TEST_CASES:
        # In a real scenario, you would run the LLM on the transcript
        # and get the predicted extraction
        test_cases_with_predictions.append({
            "predicted": test_case["gold_standard"],  # Placeholder - replace with actual LLM output
            "gold_standard": test_case["gold_standard"]
        })
    
    return generate_evaluation_report(test_cases_with_predictions) 

if __name__ == "__main__":
    print(run_evaluation_on_samples())