"""
Database initialization utilities for Supabase.

This module provides helper functions to verify the required tables exist
in Supabase and create them if necessary. This is primarily for development
and should be used carefully in production.
"""
from typing import List, Dict, Any
from supabase_client import supabase_admin_client


def check_table_exists(table_name: str) -> bool:
    """
    Check if a table exists in Supabase.
    
    Args:
        table_name: Name of the table to check
        
    Returns:
        True if the table exists, False otherwise
    """
    try:
        # Try to select one row from the table
        result = supabase_admin_client.table(table_name).select('*').limit(1).execute()
        # If we get here, the table exists
        return True
    except Exception as e:
        # If the table doesn't exist, an error will be raised
        if "relation" in str(e) and "does not exist" in str(e):
            return False
        # Re-raise any other errors
        raise


def get_required_tables() -> List[str]:
    """
    Get a list of tables required by the application.
    
    Returns:
        List of table names
    """
    return [
        'projects',
        'csd_items',
        'product_vision_boards',
        'business_model_canvases',
        'rice_items',
        'roadmap_items',
        'objectives',
        'key_results'
    ]


def verify_db_setup() -> Dict[str, bool]:
    """
    Verify that all required tables exist in the database.
    
    Returns:
        Dictionary with table names as keys and existence status as values
    """
    tables = get_required_tables()
    result = {}
    
    for table in tables:
        result[table] = check_table_exists(table)
    
    return result


def print_db_status():
    """
    Print the status of the database tables.
    
    This can be used to check if all required tables exist.
    """
    table_status = verify_db_setup()
    print("Database Status:")
    print("-" * 50)
    
    for table, exists in table_status.items():
        status = "✅ Exists" if exists else "❌ Missing"
        print(f"{table}: {status}")
    
    print("-" * 50)
    missing = [table for table, exists in table_status.items() if not exists]
    
    if missing:
        print("Missing tables:")
        for table in missing:
            print(f"  - {table}")
        print("\nPlease create these tables in Supabase or use the SQL scripts in the 'scripts' directory.")
    else:
        print("All required tables exist!")
    
    print("-" * 50) 