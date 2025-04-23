import logging
from supabase import create_client, Client
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global client using service role key (for backend operations)
try:
    logger.info("Initializing Supabase admin client...")
    supabase_admin_client = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )
    logger.info("Supabase admin client initialized successfully")
    
    # Simple validation that the client was created with the right URL
    if hasattr(supabase_admin_client, 'supabase_url'):
        logger.info(f"Supabase URL: {supabase_admin_client.supabase_url}")
    else:
        logger.info("Client initialized, but URL attribute not found")
except Exception as e:
    logger.error(f"Failed to initialize Supabase admin client: {str(e)}")
    raise

# Client factory function using anon key (for authenticated user operations through RLS)
def create_supabase_client() -> Client:
    """
    Create a new Supabase client instance using the anon key.
    This client will rely on Row Level Security (RLS) policies in Supabase
    for data access control based on the authenticated user.
    """
    try:
        logger.info("Creating new Supabase client...")
        client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key
        )
        logger.info("Supabase client created successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to create Supabase client: {str(e)}")
        raise 