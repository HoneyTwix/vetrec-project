"""
PDF Text Extraction Utility

This module provides functionality to extract text from PDF files with proper error handling
and fallback mechanisms for different PDF formats and structures.
"""

import io
import logging
from typing import Optional, Tuple
import pdfplumber
from PyPDF2 import PdfReader
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_content: bytes, filename: str = "unknown.pdf") -> Tuple[str, bool]:
    """
    Extract text from PDF content using multiple methods with fallback.
    
    Args:
        pdf_content: PDF file content as bytes
        filename: Original filename for logging purposes
        
    Returns:
        Tuple of (extracted_text, success_flag)
        - extracted_text: The extracted text or error message
        - success_flag: True if text was successfully extracted, False otherwise
    """
    
    # Method 1: Try pdfplumber (best for most PDFs)
    try:
        text = _extract_with_pdfplumber(pdf_content)
        if text and text.strip():
            logger.info(f"Successfully extracted text from {filename} using pdfplumber")
            return text, True
    except Exception as e:
        logger.warning(f"pdfplumber failed for {filename}: {str(e)}")
    
    # Method 2: Try PyMuPDF (good for scanned PDFs and complex layouts)
    try:
        text = _extract_with_pymupdf(pdf_content)
        if text and text.strip():
            logger.info(f"Successfully extracted text from {filename} using PyMuPDF")
            return text, True
    except Exception as e:
        logger.warning(f"PyMuPDF failed for {filename}: {str(e)}")
    
    # Method 3: Try PyPDF2 (basic fallback)
    try:
        text = _extract_with_pypdf2(pdf_content)
        if text and text.strip():
            logger.info(f"Successfully extracted text from {filename} using PyPDF2")
            return text, True
    except Exception as e:
        logger.warning(f"PyPDF2 failed for {filename}: {str(e)}")
    
    # All methods failed
    error_msg = f"""PDF Text Extraction Failed

File: {filename}
Size: {len(pdf_content)} bytes

This PDF could not be processed. Possible reasons:
- The PDF is password-protected
- The PDF contains only images (scanned document)
- The PDF is corrupted or in an unsupported format
- The PDF uses non-standard text encoding

Recommendations:
1. Try converting the PDF to text using a PDF reader application
2. Use OCR software if the PDF contains scanned images
3. Copy and paste the text content manually
4. Contact the document provider for a text version

If you believe this is an error, please try uploading a different PDF file."""
    
    logger.error(f"All PDF extraction methods failed for {filename}")
    return error_msg, False

def _extract_with_pdfplumber(pdf_content: bytes) -> str:
    """Extract text using pdfplumber library."""
    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
        text_parts = []
        for page_num, page in enumerate(pdf.pages, 1):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- Page {page_num} ---\n{page_text}")
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num}: {str(e)}")
                continue
        
        return "\n\n".join(text_parts)

def _extract_with_pymupdf(pdf_content: bytes) -> str:
    """Extract text using PyMuPDF (fitz) library."""
    doc = fitz.open(stream=pdf_content, filetype="pdf")
    text_parts = []
    
    for page_num in range(len(doc)):
        try:
            page = doc.load_page(page_num)
            page_text = page.get_text()
            if page_text:
                text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")
        except Exception as e:
            logger.warning(f"Failed to extract text from page {page_num + 1}: {str(e)}")
            continue
    
    doc.close()
    return "\n\n".join(text_parts)

def _extract_with_pypdf2(pdf_content: bytes) -> str:
    """Extract text using PyPDF2 library (basic fallback)."""
    pdf_reader = PdfReader(io.BytesIO(pdf_content))
    text_parts = []
    
    for page_num, page in enumerate(pdf_reader.pages, 1):
        try:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"--- Page {page_num} ---\n{page_text}")
        except Exception as e:
            logger.warning(f"Failed to extract text from page {page_num}: {str(e)}")
            continue
    
    return "\n\n".join(text_parts)

def is_pdf_file(filename: str) -> bool:
    """Check if a filename represents a PDF file."""
    return filename.lower().endswith('.pdf')

def get_pdf_info(pdf_content: bytes, filename: str = "unknown.pdf") -> dict:
    """
    Get basic information about a PDF file.
    
    Returns:
        Dictionary with PDF metadata
    """
    info = {
        "filename": filename,
        "size_bytes": len(pdf_content),
        "size_mb": round(len(pdf_content) / (1024 * 1024), 2),
        "pages": 0,
        "is_encrypted": False,
        "text_extractable": False
    }
    
    try:
        # Try to get basic info with pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            info["pages"] = len(pdf.pages)
            info["is_encrypted"] = pdf.is_encrypted
            
            # Check if text is extractable by trying the first page
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()
                info["text_extractable"] = bool(first_page_text and first_page_text.strip())
                
    except Exception as e:
        logger.warning(f"Could not get PDF info for {filename}: {str(e)}")
        # Try with PyPDF2 as fallback
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_content))
            info["pages"] = len(pdf_reader.pages)
            info["is_encrypted"] = pdf_reader.is_encrypted
        except Exception:
            pass
    
    return info 