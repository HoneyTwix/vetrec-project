"""
Utility functions for converting Clerk user IDs to database user IDs
"""
import hashlib
import logging
from typing import Optional
from sqlalchemy import select
from db.models import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clerk_id_to_int(clerk_id: str) -> int:
    """
    Convert a Clerk user ID (string) to an integer for database storage.
    Uses SHA-256 hash to ensure better uniqueness.
    """
    # Create a hash of the full Clerk ID using SHA-256 for better uniqueness
    hash_object = hashlib.sha256(clerk_id.encode())
    hash_hex = hash_object.hexdigest()
    # Take first 16 characters (8 bytes) for better uniqueness
    # Convert to positive integer by taking modulo of a large number
    large_int = int(hash_hex[:16], 16)
    return large_int % (2**31 - 1)  # Keep within SQLite INTEGER range

async def get_or_create_user_id(clerk_id: str, db_session) -> int:
    """
    Get existing user ID or create a new user record for the Clerk ID.
    Returns the integer user ID.
    """
    logger.info(f"Processing Clerk ID: {clerk_id[:12]}...")
    
    # First, try to find an existing user with this Clerk ID by searching for the email pattern
    email_pattern = f"user_{clerk_id[:8]}"
    result = await db_session.execute(
        select(User).where(User.email.like(f"{email_pattern}%"))
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        logger.info(f"✅ Found existing user - DB User ID: {existing_user.id}, Email: {existing_user.email}")
        return existing_user.id
    
    # No existing user found, create a new one
    user_id = clerk_id_to_int(clerk_id)
    logger.info(f"Creating new user - DB User ID: {user_id}")
    
    # Create new user record with unique email
    new_user = User(
        id=user_id,
        email=f"user_{clerk_id[:8]}_{user_id}@clerk.com",  # Include user_id for uniqueness
        name=f"User {clerk_id[:8]}"  # Placeholder name
    )
    db_session.add(new_user)
    await db_session.commit()
    logger.info(f"✅ New user created successfully - DB User ID: {user_id}, Email: {new_user.email}")
    
    return user_id 