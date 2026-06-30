from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database.client import get_supabase_client

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Validates the Supabase JWT token and returns the user_id.
    """
    token = credentials.credentials
    client = get_supabase_client()
    
    try:
        # Ask Supabase to verify the token and get the user
        user_response = client.auth.get_user(token)
        
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
            
        return user_response.user.id
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
