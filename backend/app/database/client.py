from supabase import Client, create_client, ClientOptions
import httpx
from app.core.config import settings

# Disable HTTP/2 to prevent httpcore.RemoteProtocolError on Hugging Face
_custom_httpx = httpx.Client(http2=False)

# Create a Singleton client so we don't exhaust connection pools
_supabase_client = create_client(
    settings.supabase_url, 
    settings.supabase_service_role_key,
    options=ClientOptions(httpx_client=_custom_httpx)
)

def get_supabase_client() -> Client:
    return _supabase_client
