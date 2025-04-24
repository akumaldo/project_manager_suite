from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
import uuid
from supabase_client import create_client, supabase_admin_client
from schemas.framework_links import (
    FrameworkLinkCreate,
    FrameworkLinkResponse,
    FrameworkLinkUpdate,
    LinkedItemsResponse,
    LinkedItemSnippet
)
from auth import get_current_user

router = APIRouter()


@router.post("/links", response_model=FrameworkLinkResponse)
async def create_framework_link(
    link_data: FrameworkLinkCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new link between framework items.
    """
    try:
        # Extract user_id from current_user dict
        user_id = current_user["user_id"]
        print(f"Creating link with user_id: {user_id}")
        
        # Add the user_id to the link data
        data = {**link_data.dict(), "user_id": str(user_id)}
        print(f"Link data: {data}")
        
        # Insert the new link
        response = supabase_admin_client.table("framework_links").insert(data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create link"
            )
        
        print(f"Created link: {response.data[0]}")
        return response.data[0]
    except Exception as e:
        print(f"Error creating link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.delete("/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_framework_link(
    link_id: uuid.UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a framework link by ID.
    """
    try:
        # Extract user_id from current_user dict
        user_id = current_user["user_id"]
        print(f"Deleting link {link_id} for user_id: {user_id}")
        
        # Check if the link exists and belongs to the user
        response = supabase_admin_client.table("framework_links") \
            .select("id") \
            .eq("id", str(link_id)) \
            .eq("user_id", str(user_id)) \
            .execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found or you don't have permission to delete it"
            )
        
        # Delete the link
        supabase_admin_client.table("framework_links") \
            .delete() \
            .eq("id", str(link_id)) \
            .execute()
        
        print(f"Successfully deleted link {link_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.get("/items/{item_type}/{item_id}/links", response_model=LinkedItemsResponse)
async def get_links_for_item(
    item_type: str,
    item_id: uuid.UUID,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all links associated with a specific item.
    """
    try:
        # Extract the user_id from the current_user dict
        user_id = current_user["user_id"]
        
        # Get links where the item is either source or target
        source_links = supabase_admin_client.table("framework_links") \
            .select("id, target_item_id, target_item_type, link_type") \
            .eq("source_item_id", str(item_id)) \
            .eq("source_item_type", item_type) \
            .eq("user_id", str(user_id)) \
            .execute()
        
        target_links = supabase_admin_client.table("framework_links") \
            .select("id, source_item_id, source_item_type, link_type") \
            .eq("target_item_id", str(item_id)) \
            .eq("target_item_type", item_type) \
            .eq("user_id", str(user_id)) \
            .execute()
        
        linked_items = []
        
        # Process source links (item is source, showing targets)
        for link in source_links.data:
            item_snippet = await get_item_snippet(
                link["target_item_type"], 
                link["target_item_id"]
            )
            if item_snippet:
                linked_items.append(item_snippet)
        
        # Process target links (item is target, showing sources)
        for link in target_links.data:
            item_snippet = await get_item_snippet(
                link["source_item_type"], 
                link["source_item_id"]
            )
            if item_snippet:
                linked_items.append(item_snippet)
        
        return {"items": linked_items}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


async def get_item_snippet(item_type: str, item_id: str) -> Optional[LinkedItemSnippet]:
    """
    Get a snippet of content from an item based on its type and ID.
    """
    try:
        # Map item_type to table and content field
        type_to_table = {
            "csd_item": {"table": "csd_items", "content_field": "text", "name_field": None},
            "roadmap_item": {"table": "roadmap_items", "content_field": "description", "name_field": "name"},
            "persona_detail": {"table": "persona_details", "content_field": "content", "name_field": None},
            "okr_key_result": {"table": "key_results", "content_field": "description", "name_field": "title"},
            "objective": {"table": "objectives", "content_field": "description", "name_field": "title"},
            "rice_item": {"table": "rice_items", "content_field": "description", "name_field": "name"},
            # Add more mappings as needed
        }
        
        if item_type not in type_to_table:
            return None
        
        mapping = type_to_table[item_type]
        
        # Query to get content and name (if available)
        query = supabase_admin_client.table(mapping["table"]).select("id")
        
        if mapping["content_field"]:
            query = query.select(mapping["content_field"])
        
        if mapping["name_field"]:
            query = query.select(mapping["name_field"])
        
        result = query.eq("id", item_id).execute()
        
        if not result.data:
            return None
        
        item_data = result.data[0]
        
        # Extract content and name
        content = item_data.get(mapping["content_field"], "") if mapping["content_field"] else ""
        name = item_data.get(mapping["name_field"], "") if mapping["name_field"] else None
        
        # Truncate content if it's too long
        if len(content) > 100:
            content = content[:97] + "..."
        
        return LinkedItemSnippet(
            id=item_data["id"],
            type=item_type,
            content=content,
            name=name
        )
    except Exception:
        return None 