from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from dependencies import get_db
from db import crud, schema, models
from utils.user_id_converter import get_or_create_user_id
from utils.pdf_extractor import extract_text_from_pdf, is_pdf_file, get_pdf_info

router = APIRouter()

@router.post("/sops", response_model=schema.SOPResponse)
async def create_sop(
    sop_data: schema.SOPCreate,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Create a new SOP for a user
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = get_or_create_user_id(user_id, db)
        
        # Create the SOP
        db_sop = crud.create_sop(db, db_user_id, sop_data)
        
        return schema.SOPResponse.from_orm(db_sop)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create SOP: {str(e)}")

@router.get("/sops/{user_id}", response_model=List[schema.SOPResponse])
async def get_user_sops(
    user_id: str,
    active_only: bool = True,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all SOPs for a user with optional filtering
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = get_or_create_user_id(user_id, db)
        
        if search:
            # Search SOPs
            sops = crud.search_sops(db, db_user_id, search)
        elif category:
            # Get SOPs by category
            sops = crud.get_sops_by_category(db, db_user_id, category)
        else:
            # Get all SOPs
            sops = crud.get_user_sops(db, db_user_id, active_only)
        
        return [schema.SOPResponse.from_orm(sop) for sop in sops]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve SOPs: {str(e)}")

@router.get("/sops/{user_id}/categories")
async def get_sop_categories(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all unique categories used by SOPs for a user
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = get_or_create_user_id(user_id, db)
        
        # Get all user's SOPs
        sops = crud.get_user_sops(db, db_user_id, active_only=False)
        
        # Extract unique categories
        categories = set()
        for sop in sops:
            if sop.category:
                categories.add(sop.category)
        
        return {"categories": sorted(list(categories))}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve categories: {str(e)}")

@router.get("/sops/{user_id}/{sop_id}", response_model=schema.SOPResponse)
async def get_sop(
    user_id: str,
    sop_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific SOP by ID
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = get_or_create_user_id(user_id, db)
        
        # Get the SOP and verify ownership
        sop = crud.get_sop(db, sop_id)
        if not sop or sop.user_id != db_user_id:
            raise HTTPException(status_code=404, detail="SOP not found")
        
        return schema.SOPResponse.from_orm(sop)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve SOP: {str(e)}")

@router.put("/sops/{user_id}/{sop_id}", response_model=schema.SOPResponse)
async def update_sop(
    user_id: str,
    sop_id: int,
    sop_data: schema.SOPUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing SOP
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = get_or_create_user_id(user_id, db)
        
        # Update the SOP
        updated_sop = crud.update_sop(db, sop_id, db_user_id, sop_data)
        if not updated_sop:
            raise HTTPException(status_code=404, detail="SOP not found")
        
        return schema.SOPResponse.from_orm(updated_sop)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update SOP: {str(e)}")

@router.delete("/sops/{user_id}/{sop_id}")
async def delete_sop(
    user_id: str,
    sop_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an SOP
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = get_or_create_user_id(user_id, db)
        
        # Delete the SOP
        success = crud.delete_sop(db, sop_id, db_user_id)
        if not success:
            raise HTTPException(status_code=404, detail="SOP not found")
        
        return {"message": "SOP deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete SOP: {str(e)}")

@router.post("/sops/{user_id}/upload")
async def upload_sop_file(
    user_id: str,
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    priority: int = 1,
    db: Session = Depends(get_db)
):
    """
    Upload an SOP from a file (text, markdown, JSON, or PDF)
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = get_or_create_user_id(user_id, db)
        
        # Read file content
        content = await file.read()
        
        # Handle different file types
        if file.filename and is_pdf_file(file.filename):
            # Extract text from PDF
            content_str, success = extract_text_from_pdf(content, file.filename)
            
            if not success:
                # PDF extraction failed - store the error message
                content_str = f"PDF EXTRACTION FAILED\n\n{content_str}"
        else:
            # For text files, decode as UTF-8
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError:
                # Try with different encoding if UTF-8 fails
                try:
                    content_str = content.decode('latin-1')
                except:
                    content_str = f"[ENCODING ERROR: {file.filename}]\n\nCould not decode file content. Please ensure the file is saved with UTF-8 encoding."
        
        # Parse tags if provided
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Use filename as title if not provided
        if not title:
            title = file.filename or "Uploaded SOP"
        
        # Create SOP data
        sop_data = schema.SOPCreate(
            title=title,
            description=description,
            content=content_str,
            category=category,
            tags=tag_list,
            priority=priority,
            is_active=True
        )
        
        # Create the SOP
        db_sop = crud.create_sop(db, db_user_id, sop_data)
        
        return {
            "message": "SOP uploaded successfully",
            "sop": schema.SOPResponse.from_orm(db_sop)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload SOP: {str(e)}")

@router.post("/sops/{user_id}/bulk-upload")
async def bulk_upload_sops(
    user_id: str,
    files: List[UploadFile] = File(...),
    descriptions: str = Form(...),  # Required: JSON string mapping filenames to descriptions
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload multiple SOPs at once with optional custom descriptions
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = get_or_create_user_id(user_id, db)
        
        # Parse tags if provided
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Parse descriptions - now required
        try:
            descriptions_dict = json.loads(descriptions)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid descriptions format. Must be valid JSON.")
        
        uploaded_sops = []
        errors = []
        
        for i, file in enumerate(files):
            try:
                # Read file content
                content = await file.read()
                
                # Handle different file types
                if file.filename and is_pdf_file(file.filename):
                    # Extract text from PDF
                    content_str, success = extract_text_from_pdf(content, file.filename)
                    
                    if not success:
                        # PDF extraction failed - store the error message
                        content_str = f"PDF EXTRACTION FAILED\n\n{content_str}"
                else:
                    # For text files, decode as UTF-8
                    try:
                        content_str = content.decode('utf-8')
                    except UnicodeDecodeError:
                        # Try with different encoding if UTF-8 fails
                        try:
                            content_str = content.decode('latin-1')
                        except:
                            content_str = f"[ENCODING ERROR: {file.filename}]\n\nCould not decode file content. Please ensure the file is saved with UTF-8 encoding."
                
                # Get custom description for this file - descriptions are now mandatory
                custom_description = descriptions_dict.get(file.filename) if file.filename else None
                if not custom_description:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Description is required for file: {file.filename}"
                    )
                
                description = custom_description
                
                # Create SOP data
                sop_data = schema.SOPCreate(
                    title=file.filename or f"Uploaded SOP {i+1}",
                    description=description,
                    content=content_str,
                    category=category,
                    tags=tag_list,
                    priority=1,
                    is_active=True
                )
                
                # Create the SOP
                db_sop = crud.create_sop(db, db_user_id, sop_data)
                uploaded_sops.append(schema.SOPResponse.from_orm(db_sop))
                
            except Exception as e:
                errors.append(f"Failed to upload {file.filename}: {str(e)}")
        
        return {
            "message": f"Uploaded {len(uploaded_sops)} SOPs successfully",
            "uploaded_sops": uploaded_sops,
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk upload SOPs: {str(e)}")

@router.post("/sops/{user_id}/analyze-pdf")
async def analyze_pdf_file(
    user_id: str,
    file: UploadFile = File(...)
):
    """
    Analyze a PDF file to provide information about its structure and extraction potential
    """
    try:
        # Read file content
        content = await file.read()
        
        if not file.filename or not is_pdf_file(file.filename):
            raise HTTPException(status_code=400, detail="File is not a PDF")
        
        # Get PDF information
        pdf_info = get_pdf_info(content, file.filename)
        
        # Try to extract a sample of text to assess quality
        sample_text, success = extract_text_from_pdf(content, file.filename)
        
        # Truncate sample text for preview
        preview_text = sample_text[:500] + "..." if len(sample_text) > 500 else sample_text
        
        analysis = {
            "filename": pdf_info["filename"],
            "file_size_mb": pdf_info["size_mb"],
            "pages": pdf_info["pages"],
            "is_encrypted": pdf_info["is_encrypted"],
            "text_extractable": pdf_info["text_extractable"],
            "extraction_success": success,
            "preview_text": preview_text if success else None,
            "recommendations": []
        }
        
        # Generate recommendations based on analysis
        if pdf_info["is_encrypted"]:
            analysis["recommendations"].append("PDF is password-protected. Please remove password protection before upload.")
        
        if not pdf_info["text_extractable"]:
            analysis["recommendations"].append("PDF appears to contain only images (scanned document). Consider using OCR software.")
        
        if pdf_info["size_mb"] > 10:
            analysis["recommendations"].append("Large PDF file. Consider splitting into smaller files for better processing.")
        
        if pdf_info["pages"] > 50:
            analysis["recommendations"].append("PDF has many pages. Consider extracting relevant sections only.")
        
        if not analysis["recommendations"]:
            analysis["recommendations"].append("PDF appears suitable for text extraction.")
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze PDF: {str(e)}") 