from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
from dependencies import get_async_db
from db import async_crud, schema, models
from utils.user_id_converter import get_or_create_user_id
from utils.pdf_extractor import extract_text_from_pdf, is_pdf_file, get_pdf_info

router = APIRouter()

@router.post("/sops", response_model=schema.SOPResponse)
async def create_sop(
    sop_data: schema.SOPCreate,
    user_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new SOP for a user
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Create the SOP
        db_sop = await async_crud.create_sop(db, db_user_id, sop_data)
        
        return schema.SOPResponse.from_orm(db_sop)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create SOP: {str(e)}")

@router.get("/sops/{user_id}", response_model=List[schema.SOPResponse])
async def get_user_sops(
    user_id: str,
    active_only: bool = True,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all SOPs for a user with optional filtering
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = await get_or_create_user_id(user_id, db)
        
        if search:
            # Search SOPs
            sops = await async_crud.search_sops(db, db_user_id, search)
        elif category:
            # Get SOPs by category
            sops = await async_crud.get_sops_by_category(db, db_user_id, category)
        else:
            # Get all SOPs
            sops = await async_crud.get_user_sops(db, db_user_id, active_only)
        
        return [schema.SOPResponse.from_orm(sop) for sop in sops]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve SOPs: {str(e)}")

@router.get("/sops/{user_id}/categories")
async def get_sop_categories(
    user_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all unique categories used by SOPs for a user
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Get all user's SOPs
        sops = await async_crud.get_user_sops(db, db_user_id, active_only=False)
        
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific SOP by ID
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Get the SOP
        sop = await async_crud.get_sop(db, db_user_id, sop_id)
        
        if not sop:
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update an existing SOP
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Update the SOP
        updated_sop = await async_crud.update_sop(db, db_user_id, sop_id, sop_data)
        
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete an SOP (soft delete by setting is_active to False)
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Delete the SOP
        success = await async_crud.delete_sop(db, db_user_id, sop_id)
        
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
    db: AsyncSession = Depends(get_async_db)
):
    """
    Upload a PDF file and create an SOP from it
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Validate file type
        if not is_pdf_file(file.filename):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        pdf_content_bytes = await file.read()
        
        # Extract text from PDF
        pdf_content, success = extract_text_from_pdf(pdf_content_bytes, file.filename)
        
        if not success:
            raise HTTPException(status_code=400, detail=f"Could not extract text from PDF: {pdf_content}")
        
        # Use filename as title if not provided
        if not title:
            title = file.filename.replace('.pdf', '').replace('_', ' ').title()
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        # Create SOP data
        sop_data = schema.SOPCreate(
            title=title,
            description=description or f"Uploaded from {file.filename}",
            content=pdf_content,
            category=category,
            tags=tag_list,
            priority=priority
        )
        
        # Create the SOP
        db_sop = await async_crud.create_sop(db, db_user_id, sop_data)
        
        return {
            "message": "SOP created successfully from PDF",
            "sop": schema.SOPResponse.from_orm(db_sop)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload SOP: {str(e)}")

@router.post("/sops/{user_id}/bulk-upload")
async def bulk_upload_sops(
    user_id: str,
    files: List[UploadFile] = File(...),
    descriptions: str = Form(...),  # Required: JSON string mapping filenames to descriptions
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Upload multiple PDF files and create SOPs from them
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Parse descriptions JSON
        try:
            descriptions_dict = json.loads(descriptions)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid descriptions JSON format")
        
        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        results = []
        errors = []
        
        for file in files:
            try:
                # Validate file type
                if not is_pdf_file(file.filename):
                    errors.append(f"{file.filename}: Only PDF files are supported")
                    continue
                
                # Read file content
                pdf_content_bytes = await file.read()
                
                # Extract text from PDF
                pdf_content, success = extract_text_from_pdf(pdf_content_bytes, file.filename)
                
                if not success:
                    errors.append(f"{file.filename}: Could not extract text from PDF")
                    continue
                
                # Get description for this file
                description = descriptions_dict.get(file.filename, f"Uploaded from {file.filename}")
                
                # Use filename as title
                title = file.filename.replace('.pdf', '').replace('_', ' ').title()
                
                # Create SOP data
                sop_data = schema.SOPCreate(
                    title=title,
                    description=description,
                    content=pdf_content,
                    category=category,
                    tags=tag_list,
                    priority=1
                )
                
                # Create the SOP
                db_sop = await async_crud.create_sop(db, db_user_id, sop_data)
                
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "sop_id": db_sop.id
                })
                
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
        
        return {
            "message": f"Bulk upload completed. {len(results)} successful, {len(errors)} failed.",
            "results": results,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to bulk upload SOPs: {str(e)}")

@router.post("/sops/{user_id}/analyze-pdf")
async def analyze_pdf_file(
    user_id: str,
    file: UploadFile = File(...)
):
    """
    Analyze a PDF file and return its information without creating an SOP
    """
    try:
        # Validate file type
        if not is_pdf_file(file.filename):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        pdf_content_bytes = await file.read()
        
        # Get PDF info
        pdf_info = get_pdf_info(pdf_content_bytes, file.filename)
        
        # Extract text from PDF
        pdf_content, success = extract_text_from_pdf(pdf_content_bytes, file.filename)
        
        if not success:
            raise HTTPException(status_code=400, detail=f"Could not extract text from PDF: {pdf_content}")
        
        # Analyze content
        word_count = len(pdf_content.split())
        char_count = len(pdf_content)
        
        # Estimate reading time (average 200 words per minute)
        reading_time_minutes = max(1, word_count // 200)
        
        return {
            "filename": file.filename,
            "pdf_info": pdf_info,
            "content_preview": pdf_content[:500] + "..." if len(pdf_content) > 500 else pdf_content,
            "statistics": {
                "word_count": word_count,
                "character_count": char_count,
                "estimated_reading_time_minutes": reading_time_minutes
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze PDF: {str(e)}") 