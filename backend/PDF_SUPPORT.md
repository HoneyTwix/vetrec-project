# PDF Support for SOP Uploads

This document describes the PDF text extraction functionality implemented for Standard Operating Procedure (SOP) uploads.

## Overview

The system now supports uploading PDF files as SOPs, with automatic text extraction and analysis capabilities. PDF files are converted to text and stored in the database for use in medical action extraction.

## Features

### 1. Multi-Library PDF Text Extraction
The system uses three different PDF libraries for robust text extraction:

- **pdfplumber** (Primary): Best for most PDFs with good text layout preservation
- **PyMuPDF** (Secondary): Good for scanned PDFs and complex layouts
- **PyPDF2** (Fallback): Basic text extraction for simple PDFs

### 2. PDF Analysis
Before upload, users can analyze PDF files to get information about:
- File size and number of pages
- Whether the PDF is encrypted
- Text extraction potential
- Preview of extracted text
- Recommendations for optimal processing

### 3. Error Handling
Comprehensive error handling for:
- Password-protected PDFs
- Corrupted PDF files
- Scanned documents (image-only PDFs)
- Unsupported PDF formats
- Large files that may cause processing issues

## Installation

### Backend Dependencies

Add the following to your `requirements.txt`:

```txt
# PDF text extraction
pdfplumber>=0.10.3
PyPDF2>=3.0.0
PyMuPDF>=1.23.0
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Frontend

1. **Upload PDFs**: Users can upload PDF files through the SOP Manager interface
2. **Analyze PDFs**: Click "Analyze PDF" button to get detailed information about the file
3. **Bulk Upload**: Upload multiple PDFs at once with automatic processing

### Backend API

#### Upload Single PDF
```http
POST /api/v1/sops/{user_id}/upload
Content-Type: multipart/form-data

file: [PDF file]
title: "Optional title"
description: "Optional description"
category: "Optional category"
tags: "comma,separated,tags"
priority: 1
```

#### Bulk Upload PDFs
```http
POST /api/v1/sops/{user_id}/bulk-upload
Content-Type: multipart/form-data

files: [PDF files]
category: "Optional category"
tags: "comma,separated,tags"
```

#### Analyze PDF
```http
POST /api/v1/sops/{user_id}/analyze-pdf
Content-Type: multipart/form-data

file: [PDF file]
```

## Technical Implementation

### PDF Extraction Utility (`utils/pdf_extractor.py`)

The core PDF processing functionality is implemented in `utils/pdf_extractor.py`:

```python
from utils.pdf_extractor import extract_text_from_pdf, get_pdf_info, is_pdf_file

# Extract text from PDF
text, success = extract_text_from_pdf(pdf_content, filename)

# Get PDF metadata
info = get_pdf_info(pdf_content, filename)

# Check if file is PDF
is_pdf = is_pdf_file(filename)
```

### Extraction Process

1. **File Detection**: Check if uploaded file is a PDF
2. **Text Extraction**: Try multiple libraries in order of preference
3. **Error Handling**: Provide detailed error messages for failed extractions
4. **Content Storage**: Store extracted text or error message in database

### Supported PDF Types

- **Text-based PDFs**: Standard PDFs with embedded text (best support)
- **Scanned PDFs**: Image-based PDFs (limited text extraction)
- **Multi-page PDFs**: PDFs with multiple pages
- **Complex Layouts**: PDFs with tables, columns, etc.

### Limitations

- **Password-protected PDFs**: Cannot be processed (user must remove password)
- **Image-only PDFs**: Limited text extraction (may need OCR)
- **Very large PDFs**: May cause memory issues (>50MB)
- **Corrupted PDFs**: May fail extraction

## Testing

### Run PDF Extraction Tests

```bash
cd backend
python test_pdf_extraction.py
```

### Test with Specific PDF

```bash
python test_pdf_extraction.py path/to/your/file.pdf
```

## Error Messages

The system provides helpful error messages for common PDF issues:

- **Password Protection**: "PDF is password-protected. Please remove password protection before upload."
- **Scanned Document**: "PDF appears to contain only images (scanned document). Consider using OCR software."
- **Large File**: "Large PDF file. Consider splitting into smaller files for better processing."
- **Many Pages**: "PDF has many pages. Consider extracting relevant sections only."

## Best Practices

### For Users

1. **Remove Passwords**: Ensure PDFs are not password-protected
2. **Use Text-based PDFs**: Prefer PDFs created from text documents over scanned images
3. **Reasonable File Sizes**: Keep PDFs under 10MB for optimal processing
4. **Check Quality**: Use the analysis feature to verify extraction quality

### For Developers

1. **Error Handling**: Always handle PDF extraction failures gracefully
2. **Memory Management**: Be mindful of large PDF files in memory
3. **User Feedback**: Provide clear feedback about extraction success/failure
4. **Testing**: Test with various PDF types and sizes

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all PDF libraries are installed
2. **Memory Issues**: Large PDFs may cause memory problems
3. **Encoding Issues**: Some PDFs may have encoding problems
4. **Library Conflicts**: Different PDF libraries may conflict

### Solutions

1. **Reinstall Dependencies**: `pip install --upgrade pdfplumber PyPDF2 PyMuPDF`
2. **Check File Size**: Limit PDF uploads to reasonable sizes
3. **Use Analysis**: Analyze PDFs before upload to identify issues
4. **Fallback Processing**: System automatically tries multiple extraction methods

## Future Enhancements

Potential improvements for future versions:

1. **OCR Integration**: Add OCR capabilities for scanned documents
2. **PDF Preview**: Show PDF preview in the interface
3. **Batch Processing**: Process multiple PDFs in background
4. **Format Conversion**: Convert PDFs to other formats
5. **Text Cleaning**: Improve text quality with post-processing 