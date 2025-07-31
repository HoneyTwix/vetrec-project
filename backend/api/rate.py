from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json
from dependencies import get_async_db
from db import async_crud, schema, models
from utils.user_id_converter import get_or_create_user_id
from utils.pdf_extractor import extract_text_from_pdf, is_pdf_file, get_pdf_info

router = APIRouter()

@router.post("/rate", response_model=schema.RateResponse)
async def rate(
    rate_data: schema.RateCreate,
    user_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new rate for a user
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Create the rate
        db_rate = await async_crud.create_rate(db, db_user_id, rate_data)
        
        return schema.RateResponse.from_orm(db_rate)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create rate: {str(e)}")

@router.get("/rates/{user_id}", response_model=List[schema.RateResponse])
async def get_user_rates(
    user_id: str,
    active_only: bool = True,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all rates for a user with optional filtering
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = await get_or_create_user_id(user_id, db)
        
        if search:
            # Search rates
            rates = await async_crud.search_rates(db, db_user_id, search)
        elif category:
            # Get rates by category
            sops = await async_crud.get_sops_by_category(db, db_user_id, category)
        else:
            # Get all SOPs
            sops = await async_crud.get_user_sops(db, db_user_id, active_only)
        
        return [schema.SOPResponse.from_orm(sop) for sop in sops]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve SOPs: {str(e)}")


@router.get("/rates/{user_id}/{rate_id}", response_model=schema.RateResponse)
async def get_rate(
    user_id: str,
    rate_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific rate by ID
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Get the rate
        rate = await async_crud.get_rate(db, db_user_id, rate_id)
        
        if not rate:
            raise HTTPException(status_code=404, detail="Rate not found")
        
        return schema.RateResponse.from_orm(rate)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve rate: {str(e)}")

@router.put("/rates/{user_id}/{rate_id}", response_model=schema.RateResponse)
async def update_rate(
    user_id: str,
    rate_id: int,
    rate_data: schema.RateUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update an existing rate
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Update the rate
        updated_rate = await async_crud.update_rate(db, db_user_id, rate_id, rate_data)
        
        if not updated_rate:
            raise HTTPException(status_code=404, detail="Rate not found")
        
        return schema.RateResponse.from_orm(updated_rate)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update SOP: {str(e)}")

@router.delete("/rates/{user_id}/{rate_id}")
async def delete_rate(
    user_id: str,
    rate_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete an rate (soft delete by setting is_active to False)
    """
    try:
        # Convert Clerk user ID to database user ID
        db_user_id = await get_or_create_user_id(user_id, db)
        
        # Delete the rate
        success = await async_crud.delete_rate(db, db_user_id, rate_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Rate not found")
        
        return {"message": "Rate deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete rate: {str(e)}")
