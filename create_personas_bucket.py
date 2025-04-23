#!/usr/bin/env python
"""
Script to create a 'personas' bucket in Supabase Storage with appropriate policies.
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')  # Use service role key for admin operations

# Create Supabase client
supabase: Client = create_client(supabase_url, supabase_key)

def create_personas_bucket():
    """Create the 'personas' bucket with appropriate policies."""
    try:
        # Check if bucket already exists
        existing_buckets = supabase.storage.list_buckets()
        bucket_exists = any(bucket.get('name') == 'personas' for bucket in existing_buckets)
        
        if not bucket_exists:
            print("Creating 'personas' bucket...")
            # Create the bucket
            bucket = supabase.storage.create_bucket(
                'personas',
                options={
                    'public': True,  # Makes the bucket publicly accessible
                    'file_size_limit': 5242880,  # 5MB limit
                    'allowed_mime_types': ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']
                }
            )
            print("Bucket created successfully!")
        else:
            print("Bucket 'personas' already exists.")
            
        print("\nIMPORTANT: Please configure the following policies through the Supabase dashboard:")
        print("1. Navigate to Storage → Buckets → personas → Policies")
        print("2. Add the following policies:")
        print("   - SELECT policy: Allow public read access (definition: true)")
        print("   - INSERT policy: Allow authenticated users to upload (definition: auth.role() = 'authenticated')")
        print("   - UPDATE policy: Allow authenticated users to update (definition: auth.role() = 'authenticated')")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    create_personas_bucket()
