#!/usr/bin/env python
"""
Helper script to check if a Supabase JWT token can be decoded with the configured JWT secret.
"""

import logging
from jose import jwt
import sys
from config import settings

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_token(token):
    """Try to decode a Supabase JWT token and print relevant information."""
    logger.info("Checking token...")
    
    # Log first and last part of token
    logger.info(f"Token: {token[:10]}...{token[-10:] if len(token) > 20 else ''}")
    
    # Check JWT Secret
    jwt_secret = settings.supabase_jwt_secret
    logger.info(f"JWT Secret: {jwt_secret[:5]}...{'*' * 10}")
    
    # Get header
    try:
        header = jwt.get_unverified_header(token)
        logger.info(f"Token header: {header}")
    except Exception as e:
        logger.error(f"Failed to get token header: {e}")
        return
    
    # Try to decode token without verification
    try:
        # Dummy key for unverified decoding
        dummy_key = "dummy_key"
        
        payload = jwt.decode(
            token, 
            dummy_key, 
            options={"verify_signature": False}
        )
        
        logger.info("\n=== TOKEN PAYLOAD (UNVERIFIED) ===")
        for key, value in payload.items():
            logger.info(f"{key}: {value}")
            
        # Check important fields
        logger.info("\n=== VERIFICATION CHECKS ===")
        logger.info(f"Token issuer (iss): {payload.get('iss')}")
        logger.info(f"Token audience (aud): {payload.get('aud')}")
        logger.info(f"Subject (sub): {payload.get('sub')}")
        
        # Check expiration
        import time
        exp = payload.get('exp')
        current_time = int(time.time())
        if exp:
            logger.info(f"Expiration time: {exp} ({time.ctime(exp)})")
            logger.info(f"Current time: {current_time} ({time.ctime(current_time)})")
            logger.info(f"Token is {'EXPIRED' if exp < current_time else 'valid'}")
        else:
            logger.info("No expiration time found in token")
            
    except Exception as e:
        logger.error(f"Failed to decode token without verification: {e}")
        return
    
    # Try actual verification with provided secret
    try:
        logger.info("\n=== ATTEMPTING VERIFICATION WITH SECRET ===")
        verified_payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=['HS256'],
            options={"verify_aud": False}  # Skip audience verification
        )
        logger.info("✅ TOKEN SUCCESSFULLY VERIFIED!")
    except Exception as e:
        logger.error(f"❌ TOKEN VERIFICATION FAILED: {e}")
        logger.info("\n=== VERIFICATION WORKAROUNDS ===")
        
        # See if we can find the verification issue and suggest a fix
        supabase_url = None
        if 'iss' in payload and 'supabase' in payload['iss']:
            supabase_url = payload['iss'].split('/auth')[0]
            logger.info(f"Detected Supabase URL from token: {supabase_url}")
            
            # Compare against configured URL
            if hasattr(settings, 'supabase_url'):
                if settings.supabase_url == supabase_url:
                    logger.info("✅ Supabase URL in token matches configuration")
                else:
                    logger.info(f"❌ Supabase URL MISMATCH: Config has {settings.supabase_url} but token has {supabase_url}")
            
            # Reconstruct expected JWT secret format for Supabase
            logger.info("\nFor Supabase, try using this value for SUPABASE_JWT_SECRET in your .env:")
            logger.info(f"Value should be the JWT secret from Supabase dashboard")
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.info("Usage: python check_jwt.py <jwt_token>")
        sys.exit(1)
        
    token = sys.argv[1]
    check_token(token) 