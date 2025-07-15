"""
Test script to demonstrate custom extraction categories
"""
import requests
import json

def test_custom_categories():
    """
    Test the custom categories feature with different types of custom extractions
    """
    
    # Test 1: Billing follow-up category
    print("=== Test 1: Billing Follow-up Category ===")
    
    billing_request = {
        "transcript_text": "Doctor: Patient presents with chest pain. I'm ordering an EKG and blood work. Also, please follow up with billing department about the patient's insurance coverage for the cardiac stress test we discussed.",
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
    
    response = requests.post("http://localhost:8000/api/v1/extract", json=billing_request)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ Billing extraction successful")
        if "custom_extractions" in result["extraction"]:
            print(f"Custom extractions: {json.dumps(result['extraction']['custom_extractions'], indent=2)}")
    else:
        print(f"❌ Error: {response.text}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Diagnostic reminder category
    print("=== Test 2: Diagnostic Reminder Category ===")
    
    diagnostic_request = {
        "transcript_text": "Doctor: Patient has diabetes and needs regular monitoring. Schedule HbA1c test for next month, and remind patient to check blood sugar daily. Also, we need to order a foot exam for diabetic neuropathy screening.",
        "notes": "",
        "user_id": 123,
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
    
    response = requests.post("http://localhost:8000/api/v1/extract", json=diagnostic_request)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ Diagnostic extraction successful")
        if "custom_extractions" in result["extraction"]:
            print(f"Custom extractions: {json.dumps(result['extraction']['custom_extractions'], indent=2)}")
    else:
        print(f"❌ Error: {response.text}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Multiple custom categories
    print("=== Test 3: Multiple Custom Categories ===")
    
    multiple_request = {
        "transcript_text": "Doctor: Patient with hypertension needs medication adjustment. Prescribing lisinopril 20mg daily. Schedule follow-up in 2 weeks. Also, please contact the pharmacy about the patient's prescription coverage and set up automatic refills.",
        "notes": "",
        "user_id": 123,
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
    
    response = requests.post("http://localhost:8000/api/v1/extract", json=multiple_request)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("✅ Multiple categories extraction successful")
        if "custom_extractions" in result["extraction"]:
            print(f"Custom extractions: {json.dumps(result['extraction']['custom_extractions'], indent=2)}")
    else:
        print(f"❌ Error: {response.text}")

if __name__ == "__main__":
    test_custom_categories() 