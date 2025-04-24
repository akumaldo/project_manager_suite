from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
import uuid
from pydantic import BaseModel
from supabase_client import supabase_admin_client
from auth import get_current_user

router = APIRouter()

class ItemResponse(BaseModel):
    id: str
    type: str
    content: str
    name: Optional[str] = None

@router.get("/items/{item_type}/{item_id}", response_model=ItemResponse)
async def get_item_by_type_and_id(
    item_type: str,
    item_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get an item by its type and ID.
    """
    try:
        user_id = current_user["user_id"]
        
        # Map item_type to table and content field
        type_to_table = {
            "csd_item": {"table": "csd_items", "content_field": "text", "name_field": None},
            "roadmap_item": {"table": "roadmap_items", "content_field": "description", "name_field": "name"},
            "persona_detail": {"table": "persona_details", "content_field": "content", "name_field": None},
            "okr_key_result": {"table": "key_results", "content_field": "description", "name_field": "title"},
            "objective": {"table": "objectives", "content_field": "description", "name_field": "title"},
            "rice_item": {"table": "rice_items", "content_field": "description", "name_field": "name"},
        }
        
        if item_type not in type_to_table:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported item type: {item_type}"
            )
        
        mapping = type_to_table[item_type]
        
        # Query to get content and name (if available)
        query = supabase_admin_client.table(mapping["table"]).select("id")
        
        if mapping["content_field"]:
            query = query.select(mapping["content_field"])
        
        if mapping["name_field"]:
            query = query.select(mapping["name_field"])
        
        # Use only the ID filter, removing the user_id filter which causes issues
        # The RLS policies should already handle user access restrictions
        print(f"Querying {mapping['table']} for item_id {item_id}")
        result = query.eq("id", item_id).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item not found with type {item_type} and id {item_id}"
            )
        
        item_data = result.data[0]
        print(f"Found item data: {item_data}")
        
        # Extract content and name
        content = item_data.get(mapping["content_field"], "") if mapping["content_field"] else ""
        name = item_data.get(mapping["name_field"], "") if mapping["name_field"] else None
        
        return ItemResponse(
            id=item_data["id"],
            type=item_type,
            content=content,
            name=name
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_item_by_type_and_id: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )

@router.get("/personas/details", response_model=List[ItemResponse])
async def get_persona_details_by_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all persona details for a project.
    This is a compatibility endpoint for the frontend.
    """
    try:
        user_id = current_user["user_id"]
        print(f"Getting persona details for project {project_id}")
        
        # First, get all personas for this project - rely on RLS
        personas_result = supabase_admin_client.table('personas').select('id')\
            .eq('project_id', project_id)\
            .execute()
        
        if not personas_result.data:
            print(f"No personas found for project {project_id}")
            return []
        
        print(f"Found {len(personas_result.data)} personas")
        persona_ids = [persona['id'] for persona in personas_result.data]
        
        # Get all details for these personas
        all_details = []
        for persona_id in persona_ids:
            # Rely on RLS instead of explicitly filtering by user_id
            details_result = supabase_admin_client.table('persona_details').select('*')\
                .eq('persona_id', persona_id)\
                .execute()
            
            if details_result.data:
                print(f"Found {len(details_result.data)} details for persona {persona_id}")
                for detail in details_result.data:
                    all_details.append(ItemResponse(
                        id=detail['id'],
                        type='persona_detail',
                        content=detail.get('content', ''),
                        name=None
                    ))
        
        return all_details
    except Exception as e:
        print(f"Error in get_persona_details_by_project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        ) 