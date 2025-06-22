from fastapi import Header, HTTPException, Depends
from sqlmodel import Session
from models import User # Assuming models.py is in the same directory
from database import get_session

async def get_current_user(
    x_user_id: int = Header(None), # Made optional for easier testing
    session: Session = Depends(get_session)
) -> User:
    """
    A dependency to fetch the current user from the database.
    It reads a user ID from the `X-User-Id` header.

    In a real production application, this should be replaced with a secure
    method like decoding a JWT from the 'Authorization: Bearer <token>' header.
    """
    if x_user_id is None:
        raise HTTPException(
            status_code=401, 
            detail="User ID must be provided in the 'X-User-Id' header."
        )

    user = session.get(User, x_user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User with ID {x_user_id} not found.")
    
    return user

