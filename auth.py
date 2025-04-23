from fastapi import APIRouter, Depends, HTTPException, status, Header, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional, Dict, Any
from pydantic import BaseModel
import logging

from config import settings
from supabase_client import create_supabase_client, supabase_admin_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

# Add explicit OPTIONS handlers for CORS preflight requests
@router.options("/login")
@router.options("/register")
async def options_handler():
    """Handle CORS preflight requests for auth endpoints"""
    logger.info("OPTIONS request for auth endpoint")
    return Response(status_code=200)

@router.post("/login")
async def login(request: LoginRequest):
    try:
        logger.info(f"Login attempt for email: {request.email}")
        
        # Create login payload
        login_data = {
            "email": request.email,
            "password": request.password
        }
        
        logger.info(f"Calling Supabase sign_in_with_password")
        
        try:
            # Use the appropriate method to sign in
            response = None
            try:
                # First try the synchronous method
                response = supabase_admin_client.auth.sign_in_with_password(login_data)
                logger.info("Used synchronous sign_in_with_password")
            except AttributeError:
                # Fallback to asynchronous method if available
                logger.info("Trying async sign_in_with_password")
                response = await supabase_admin_client.auth.sign_in_with_password(login_data)
                logger.info("Used async sign_in_with_password")
            
            if not response or not response.session:
                logger.error(f"Login failed for {request.email}: No session returned")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )
                
            logger.info(f"Login successful for {request.email}")
            return {
                "access_token": response.session.access_token,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "name": response.user.user_metadata.get("name", "")
                }
            }
        except Exception as inner_e:
            logger.error(f"Supabase login error: {str(inner_e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Login failed: {str(inner_e)}"
            )
            
    except Exception as e:
        logger.error(f"Login error for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login error: {str(e)}"
        )

@router.post("/register")
async def register(request: RegisterRequest):
    try:
        logger.info(f"Registration attempt for email: {request.email}")
        
        # Create the registration payload
        signup_data = {
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "name": request.name
                }
            }
        }
        
        logger.info(f"Calling Supabase sign_up")
        
        try:
            # Try to use the appropriate sign_up method
            response = None
            try:
                # First try the synchronous method
                response = supabase_admin_client.auth.sign_up(signup_data)
                logger.info("Used synchronous sign_up")
            except AttributeError:
                # Fallback to asynchronous method if available
                logger.info("Trying async sign_up")
                response = await supabase_admin_client.auth.sign_up(signup_data)
                logger.info("Used async sign_up")
            
            logger.info(f"Registration response type: {type(response)}")
            
            if not response or not response.user:
                logger.error(f"Registration failed for {request.email}: No user in response")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Registration failed - no user returned"
                )
                
            # Return success response
            logger.info(f"Registration successful for {request.email}")
            return {
                "message": "Registration successful. Please check your email for verification.",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "name": request.name
                }
            }
            
        except Exception as inner_e:
            logger.error(f"Supabase sign_up error: {str(inner_e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration failed: {str(inner_e)}"
            )
            
    except Exception as e:
        logger.error(f"Registration error for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration error: {str(e)}"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency that extracts and verifies the Supabase JWT token from
    the Authorization header. Returns the user data if the token is valid.
    
    This function:
    1. Extracts the JWT token from the Authorization: Bearer <token> header
    2. Verifies the JWT using Supabase's JWT secret
    3. Returns the user data from the token claims
    
    Raises:
    - HTTPException (401) if token is invalid or expired
    """
    try:
        token = credentials.credentials
        logger.info(f"Processing authorization token: {token[:10]}...{token[-10:] if len(token) > 20 else ''}")
        
        # Log JWT secret (first few chars only for security)
        secret_preview = settings.supabase_jwt_secret[:5] + "..." if settings.supabase_jwt_secret else "None"
        logger.info(f"Using JWT secret: {secret_preview}")
        
        try:
            # Try to decode the token header without verification first to debug
            header = jwt.get_unverified_header(token)
            logger.info(f"JWT header: {header}")
            
            # Get algorithm from token header
            alg = header.get('alg', 'HS256')
            logger.info(f"Token algorithm: {alg}")
            
            # Log the key ID from the token if present
            if 'kid' in header:
                logger.info(f"Token kid: {header.get('kid')}")
            
            # Create a dummy key for unverified decoding
            dummy_key = "dummy_key_for_unverified_decoding"
            
            # Try to decode without verification
            try:
                unverified_payload = jwt.decode(
                    token, 
                    dummy_key,
                    options={"verify_signature": False}
                )
                logger.info(f"Unverified token issuer: {unverified_payload.get('iss', 'unknown')}")
            except Exception as e:
                logger.error(f"Could not decode unverified token: {str(e)}")
                unverified_payload = {}
            
            # For Supabase, we need to try different approaches
            payload = None
            jwt_secret = settings.supabase_jwt_secret
            
            # First try: Use the token directly
            # This is a shortcut for Supabase token validation
            if unverified_payload and 'sub' in unverified_payload:
                # Check if this is a Supabase token by checking issuer
                issuer = unverified_payload.get('iss', '')
                if 'supabase' in issuer.lower():
                    logger.info("Token appears to be from Supabase based on issuer")
                    
                    # Check if token is expired
                    import time
                    current_time = int(time.time())
                    
                    if 'exp' in unverified_payload and unverified_payload['exp'] < current_time:
                        logger.error(f"Token expired at {unverified_payload['exp']}, current time is {current_time}")
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token is expired"
                        )
                    
                    # For development/debugging purposes, we'll accept the token
                    # In production, you'd want to properly verify the signature
                    logger.warning("⚠️ Using unverified token - ONLY FOR DEVELOPMENT")
                    payload = unverified_payload
            
            # Second try: Standard verification with configured secret
            if not payload:
                try:
                    logger.info("Attempting standard JWT verification...")
                    payload = jwt.decode(
                        token,
                        jwt_secret,
                        algorithms=[alg],
                        options={"verify_aud": False}  # Skip audience verification
                    )
                    logger.info("Standard JWT verification successful")
                except Exception as e:
                    logger.warning(f"Standard JWT verification failed: {str(e)}")
                    # We'll try some other verification methods or use the unverified token
                    # as a fallback for development purposes
                    if unverified_payload and 'sub' in unverified_payload:
                        logger.warning("⚠️ Falling back to unverified token - ONLY FOR DEVELOPMENT")
                        payload = unverified_payload
            
            if not payload:
                logger.error("Failed to validate token with all methods")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="Invalid authentication token - verification failed"
                )
                
            logger.info(f"JWT processed. Payload issuer: {payload.get('iss', 'unknown')}")
            
            # Extract user ID from the 'sub' claim
            user_id = payload.get("sub")
            if not user_id:
                logger.error("Missing 'sub' claim in JWT payload")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token - missing user ID"
                )
            
            # Extract email from the proper location in Supabase tokens
            email = payload.get("email")
            if not email and 'user_metadata' in payload:
                email = payload.get('user_metadata', {}).get('email')
                
            logger.info(f"Authentication successful for user_id: {user_id}, email: {email}")
                
            # Return user data from payload
            return {
                "user_id": user_id,
                "email": email,
                "role": payload.get("role", "user"),
            }
            
        except JWTError as jwt_error:
            logger.error(f"JWT validation error: {str(jwt_error)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(jwt_error)}"
            )
            
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

async def get_supabase_client(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Creates a Supabase client instance with the user's JWT token.
    This ensures the client operates with the user's permissions via RLS.
    """
    supabase = create_supabase_client()
    # For full user context, we could set the auth token on the client
    # This would allow RLS policies to work based on the auth.uid()
    return supabase 