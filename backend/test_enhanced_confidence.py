#!/usr/bin/env python3
"""
Test script for enhanced confidence system
"""

import asyncio
import json
from baml_client import b
from baml_client.types import MedicalExtraction

async def test_enhanced_confidence():
    """Test the enhanced confidence evaluation"""
    
    # Sample transcript
    transcript = """
    Doctor: Mrs. Johnson, I see your blood pressure is still elevated at 160/95. 
    I want you to return in 2 weeks for a follow-up to check your blood pressure. 
    If it's still elevated, we might need to adjust your medication. 
    Also, please make sure to take your lisinopril 10mg once daily at the same time each day.
    I'll also order some blood work to check your kidney function.
    """
    
    # Sample extraction (this would normally come from the extraction function)
    extraction = MedicalExtraction(
        follow_up_tasks=[
            {
                "description": "Schedule blood work for tomorrow",
                "priority": "high",
                "due_date": "tomorrow",
                "assigned_to": "clinician"
            },
            {
                "description": "Return for follow-up in 2 weeks",
                "priority": "medium",
                "due_date": "in 2 weeks", 
                "assigned_to": "client"
            }
        ],
        medication_instructions=[
            {
                "medication_name": "lisinopril",
                "dosage": "10mg",
                "frequency": "once daily",
                "duration": "ongoing",
                "special_instructions": "at the same time each day"
            }
        ],
        client_reminders=[
            {
                "reminder_type": "test",
                "description": "Blood work appointment tomorrow",
                "due_date": "tomorrow",
                "priority": "high"
            }
        ],
        clinician_todos=[
            {
                "task_type": "test_order",
                "description": "Order blood work including kidney function",
                "priority": "high",
                "assigned_to": "clinician",
                "due_date": "tomorrow"
            }
        ]
    )
    
    # Sample gold standard
    gold_standard = MedicalExtraction(
        follow_up_tasks=[
            {
                "description": "Schedule blood work for tomorrow",
                "priority": "high",
                "due_date": "tomorrow",
                "assigned_to": "clinician"
            },
            {
                "description": "Return for follow-up in 2 weeks",
                "priority": "medium",
                "due_date": "in 2 weeks",
                "assigned_to": "client"
            }
        ],
        medication_instructions=[
            {
                "medication_name": "lisinopril",
                "dosage": "10mg",
                "frequency": "once daily",
                "duration": "ongoing",
                "special_instructions": "at the same time each day"
            }
        ],
        client_reminders=[
            {
                "reminder_type": "test",
                "description": "Blood work appointment tomorrow",
                "due_date": "tomorrow",
                "priority": "high"
            }
        ],
        clinician_todos=[
            {
                "task_type": "test_order",
                "description": "Order blood work including kidney function",
                "priority": "high",
                "assigned_to": "clinician",
                "due_date": "tomorrow"
            }
        ]
    )
    
    try:
        print("Testing enhanced confidence evaluation...")
        
        # Test the enhanced evaluation function
        result = b.EvaluateWithSingleStandard(
            predicted_extraction=extraction,
            primary_standard=gold_standard,
            original_transcript=transcript
        )
        
        print("✓ Enhanced evaluation completed successfully!")
        print(f"Overall confidence: {result.confidence_details.overall_confidence}")
        print(f"Confidence summary: {result.confidence_details.confidence_summary}")
        
        # Print flagged sections
        print("\nFlagged sections:")
        print(f"Follow-up tasks: {result.confidence_details.flagged_sections.follow_up_tasks}")
        print(f"Medications: {result.confidence_details.flagged_sections.medication_instructions}")
        print(f"Client reminders: {result.confidence_details.flagged_sections.client_reminders}")
        print(f"Clinician todos: {result.confidence_details.flagged_sections.clinician_todos}")
        
        # Print item confidence details
        print("\nItem confidence details:")
        for i, task in enumerate(result.confidence_details.item_confidence.follow_up_tasks):
            print(f"Follow-up task {i}: {task.confidence.confidence} - {task.confidence.reasoning}")
        
        for i, med in enumerate(result.confidence_details.item_confidence.medication_instructions):
            print(f"Medication {i}: {med.confidence.confidence} - {med.confidence.reasoning}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing enhanced confidence: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_enhanced_confidence()) 