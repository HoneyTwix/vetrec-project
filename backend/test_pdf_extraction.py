#!/usr/bin/env python3
"""
Test script for PDF text extraction functionality

This script tests the PDF extraction utility with sample PDFs or creates a test PDF
to verify the extraction pipeline works correctly.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from utils.pdf_extractor import extract_text_from_pdf, get_pdf_info, is_pdf_file

def create_test_pdf():
    """
    Create a simple test PDF file for testing extraction
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            pdf_path = tmp_file.name
        
        # Create PDF content
        c = canvas.Canvas(pdf_path, pagesize=letter)
        
        # Add some test content
        c.drawString(100, 750, "Test SOP Document")
        c.drawString(100, 720, "This is a test Standard Operating Procedure document.")
        c.drawString(100, 690, "It contains multiple lines of text to test extraction.")
        c.drawString(100, 660, "The PDF should be processed correctly by our extraction utility.")
        
        # Add a second page
        c.showPage()
        c.drawString(100, 750, "Page 2 - Additional Content")
        c.drawString(100, 720, "This is the second page of our test document.")
        c.drawString(100, 690, "It demonstrates multi-page PDF processing.")
        
        c.save()
        return pdf_path
        
    except ImportError:
        print("reportlab not available, skipping test PDF creation")
        return None

def test_pdf_extraction():
    """
    Test PDF extraction functionality
    """
    print("🧪 Testing PDF Extraction Functionality")
    print("=" * 50)
    
    # Test 1: Check if PDF libraries are available
    print("\n1. Checking PDF library availability...")
    try:
        import pdfplumber
        print("✅ pdfplumber is available")
    except ImportError:
        print("❌ pdfplumber is not available")
        return False
    
    try:
        from PyPDF2 import PdfReader
        print("✅ PyPDF2 is available")
    except ImportError:
        print("❌ PyPDF2 is not available")
        return False
    
    try:
        import fitz
        print("✅ PyMuPDF is available")
    except ImportError:
        print("❌ PyMuPDF is not available")
    
    # Test 2: Create and test with a sample PDF
    print("\n2. Testing with sample PDF...")
    test_pdf_path = create_test_pdf()
    
    if test_pdf_path and os.path.exists(test_pdf_path):
        try:
            # Read the test PDF
            with open(test_pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Test PDF info extraction
            print("   Getting PDF info...")
            pdf_info = get_pdf_info(pdf_content, "test.pdf")
            print(f"   - Pages: {pdf_info['pages']}")
            print(f"   - Size: {pdf_info['size_mb']} MB")
            print(f"   - Encrypted: {pdf_info['is_encrypted']}")
            print(f"   - Text extractable: {pdf_info['text_extractable']}")
            
            # Test text extraction
            print("   Extracting text...")
            extracted_text, success = extract_text_from_pdf(pdf_content, "test.pdf")
            
            if success:
                print("✅ Text extraction successful!")
                print(f"   Extracted {len(extracted_text)} characters")
                print("   Preview:")
                print("   " + "-" * 40)
                print("   " + extracted_text[:200] + "..." if len(extracted_text) > 200 else "   " + extracted_text)
                print("   " + "-" * 40)
            else:
                print("❌ Text extraction failed")
                print("   Error message:")
                print("   " + extracted_text)
            
            # Clean up
            os.unlink(test_pdf_path)
            
        except Exception as e:
            print(f"❌ Error testing PDF extraction: {e}")
            if test_pdf_path and os.path.exists(test_pdf_path):
                os.unlink(test_pdf_path)
            return False
    
    # Test 3: Test file type detection
    print("\n3. Testing file type detection...")
    test_cases = [
        ("document.pdf", True),
        ("document.PDF", True),
        ("document.txt", False),
        ("document.docx", False),
        ("document", False),
    ]
    
    for filename, expected in test_cases:
        result = is_pdf_file(filename)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {filename}: {result} (expected {expected})")
    
    print("\n🎉 PDF extraction testing completed!")
    return True

def test_with_existing_pdf(pdf_path):
    """
    Test extraction with an existing PDF file
    """
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return False
    
    print(f"🧪 Testing with existing PDF: {pdf_path}")
    print("=" * 50)
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Get PDF info
        pdf_info = get_pdf_info(pdf_content, os.path.basename(pdf_path))
        print(f"📄 PDF Info:")
        print(f"   - Pages: {pdf_info['pages']}")
        print(f"   - Size: {pdf_info['size_mb']} MB")
        print(f"   - Encrypted: {pdf_info['is_encrypted']}")
        print(f"   - Text extractable: {pdf_info['text_extractable']}")
        
        # Extract text
        print(f"\n📝 Extracting text...")
        extracted_text, success = extract_text_from_pdf(pdf_content, os.path.basename(pdf_path))
        
        if success:
            print("✅ Text extraction successful!")
            print(f"   Extracted {len(extracted_text)} characters")
            print(f"   Preview (first 300 characters):")
            print("   " + "-" * 50)
            print("   " + extracted_text[:300] + "..." if len(extracted_text) > 300 else "   " + extracted_text)
            print("   " + "-" * 50)
        else:
            print("❌ Text extraction failed")
            print("   Error message:")
            print("   " + extracted_text)
        
        return success
        
    except Exception as e:
        print(f"❌ Error testing PDF: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with provided PDF file
        pdf_path = sys.argv[1]
        test_with_existing_pdf(pdf_path)
    else:
        # Run general tests
        test_pdf_extraction() 