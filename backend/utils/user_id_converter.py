import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clerk_id_to_int(clerk_id: str) -> int:
    """
    Convert a Clerk user ID string to a deterministic integer.
    Uses SHA-256 hash and takes the first 8 bytes as an integer.
    """
    # Create a hash of the Clerk ID
    hash_object = hashlib.sha256(clerk_id.encode())
    hash_hex = hash_object.hexdigest()
    
    # Take the first 8 characters (4 bytes) and convert to integer
    # This gives us a positive integer that's deterministic for the same Clerk ID
    integer_id = int(hash_hex[:8], 16)
    
    return integer_id

async def get_or_create_user_id(clerk_id: str, db_session) -> int:
    """
    Get existing user ID or create a new user record for the Clerk ID.
    Returns the integer user ID.
    """
    from db.models import User
    from sqlalchemy import select
    
    # Convert Clerk ID to integer
    user_id = clerk_id_to_int(clerk_id)
    
    logger.info(f"Checking if user exists in database - Clerk ID: {clerk_id[:8]}..., DB User ID: {user_id}")
    
    # Check if user already exists
    result = await db_session.execute(select(User).where(User.id == user_id))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        logger.info(f"✅ User found in database - DB User ID: {user_id}, Name: {existing_user.name}")
    else:
        logger.info(f"❌ User not found in database - Creating new user - DB User ID: {user_id}")
        # Create new user record
        new_user = User(
            id=user_id,
            email=f"user_{clerk_id[:8]}@clerk.com",  # Placeholder email
            name=f"User {clerk_id[:8]}"  # Placeholder name
        )
        db_session.add(new_user)
        await db_session.commit()
        logger.info(f"✅ New user created successfully - DB User ID: {user_id}, Name: {new_user.name}")
    
    return user_id 