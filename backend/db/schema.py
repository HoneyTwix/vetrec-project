from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

# Custom Category Models
class CustomCategory(BaseModel):
    name: str
    description: str
    field_type: str  # "text", "list", "structured"
    required_fields: Optional[List[str]] = None
    optional_fields: Optional[List[str]] = None

# User Info Model
class UserInfo(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None

# SOP Models
class SOPBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: str
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: bool = True
    priority: int = 1

class SOPCreate(SOPBase):
    pass

class SOPUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None

class SOPResponse(SOPBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Request Models
class TranscriptRequest(BaseModel):
    transcript_text: str
    notes: Optional[str] = None
    user_id: Optional[Union[int, str]] = None
    user_info: Optional[UserInfo] = None
    custom_categories: Optional[List[CustomCategory]] = None
    sop_ids: Optional[List[int]] = None  # IDs of SOPs to include in context

class FlaggedResponseRequest(BaseModel):
    transcript_id: int
    extraction_data: Dict[str, Any]
    review_notes: Optional[str] = None
    reviewed_by: Optional[str] = "human"

class UserCreate(BaseModel):
    email: str
    name: str

# Response Models
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class VisitTranscriptResponse(BaseModel):
    id: int
    user_id: Optional[Union[int, str]]
    transcript_text: str
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ExtractionResultResponse(BaseModel):
    id: int
    transcript_id: int
    follow_up_tasks: Optional[List[Dict[str, Any]]]
    medication_instructions: Optional[List[Dict[str, Any]]]
    client_reminders: Optional[List[Dict[str, Any]]]
    clinician_todos: Optional[List[Dict[str, Any]]]
    custom_extractions: Optional[Dict[str, Any]] = None  # Store custom category extractions
    evaluation_results: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Enhanced confidence models
class ItemConfidenceResponse(BaseModel):
    confidence: str  # "high" | "medium" | "low"
    reasoning: str
    issues: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None

class FlaggedSectionsResponse(BaseModel):
    follow_up_tasks: List[int] = []  # Indexes of flagged items
    medication_instructions: List[int] = []
    client_reminders: List[int] = []
    clinician_todos: List[int] = []
    custom_extractions: Optional[List[int]] = None

class ConfidenceDetailsResponse(BaseModel):
    overall_confidence: str  # "high" | "medium" | "low"
    flagged_sections: FlaggedSectionsResponse
    confidence_summary: str
    item_confidence: Optional[Dict[str, Any]] = None  # Detailed confidence for each item

class ExtractionResponse(BaseModel):
    transcript: VisitTranscriptResponse
    extraction: ExtractionResultResponse
    confidence_level: Optional[str] = None
    flagged: Optional[bool] = None
    review_required: Optional[bool] = None
    evaluation_results: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    # Enhanced confidence fields
    confidence_details: Optional[ConfidenceDetailsResponse] = None

class ReviewResponse(BaseModel):
    transcript: VisitTranscriptResponse
    extraction: Dict[str, Any]  # Raw extraction data
    confidence_level: str
    review_required: bool
    flagged: bool = True  # New field to indicate if response is flagged
    evaluation_results: Optional[Dict[str, Any]] = None
    message: str

class FlaggedResponseResponse(BaseModel):
    message: str
    extraction_id: int
    confidence_level: str = "reviewed"
    flagged: bool = False

class MemoryResponse(BaseModel):
    previous_visits: List[ExtractionResponse]
