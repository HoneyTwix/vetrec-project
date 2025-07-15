import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from baml_client import b
from typing import Optional

from db import models, schema, crud
from api.extract import router as extract_router
from api.sops import router as sops_router

# Load environment variables
load_dotenv()

# BAML client setup - b is already initialized from baml_client import

# FastAPI app
app = FastAPI(
    title="VetRec Medical Action Extraction API",
    description="API for extracting actionable items from medical visit transcripts",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Include routers
app.include_router(extract_router, prefix="/api/v1", tags=["extract"])
app.include_router(sops_router, prefix="/api/v1", tags=["sops"])

@app.get("/")
async def root():
    return {"message": "VetRec Medical Action Extraction API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
