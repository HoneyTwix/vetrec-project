import hashlib

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

def get_or_create_user_id(clerk_id: str, db_session) -> int:
    """
    Get existing user ID or create a new user record for the Clerk ID.
    Returns the integer user ID.
    """
    from db.models import User
    
    # Convert Clerk ID to integer
    user_id = clerk_id_to_int(clerk_id)
    
    # Check if user already exists
    existing_user = db_session.query(User).filter(User.id == user_id).first()
    
    if not existing_user:
        # Create new user record
        new_user = User(
            id=user_id,
            email=f"user_{clerk_id[:8]}@clerk.com",  # Placeholder email
            name=f"User {clerk_id[:8]}"  # Placeholder name
        )
        db_session.add(new_user)
        db_session.commit()
    
    return user_id 