from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Dict, Any, List

from schemas.roadmap import RoadmapItem, RoadmapItemCreate, RoadmapItemUpdate, RoadmapItemList, RoadmapItemReorder
from auth import get_current_user
from supabase_client import supabase_admin_client

router = APIRouter()


@router.get("/projects/{project_id}/roadmap", response_model=RoadmapItemList)
async def get_roadmap_items(
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all roadmap items for a specific project.
    """
    user_id = current_user["user_id"]
    
    # Verify project exists and belongs to user
    try:
        project_result = supabase_admin_client.table('projects').select('id')\
            .eq('id', project_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if not project_result.data or len(project_result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
    except Exception as e:
        print(f"Error checking for existing project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Query roadmap items with RLS filtering by user_id and project_id
    try:
        result = supabase_admin_client.table('roadmap_items').select('*')\
            .eq('project_id', project_id)\
            .eq('user_id', user_id)\
            .order('position', desc=False)\
            .execute()
        
        # Map name to content for frontend compatibility
        items = result.data or []
        for item in items:
            if 'name' in item:
                item['content'] = item.get('name', '')
        
        return RoadmapItemList(items=items)
    except Exception as e:
        print(f"Error fetching roadmap items: {str(e)}")
        # Return empty list on error
        return RoadmapItemList(items=[])


@router.post("/projects/{project_id}/roadmap", response_model=RoadmapItem, status_code=status.HTTP_201_CREATED)
async def create_roadmap_item(
    roadmap_item: RoadmapItemCreate,
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new roadmap item for a specific project.
    """
    user_id = current_user["user_id"]
    
    # Verify project exists and belongs to user
    project_result = supabase_admin_client.table('projects').select('id')\
        .eq('id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not project_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Ensure project_id in path matches project_id in request body
    if roadmap_item.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID in path must match project ID in request body"
        )
    
    # Process content field for backend storage
    roadmap_data = roadmap_item.model_dump()
    
    # If content is provided but name is not, use content as name
    if 'content' in roadmap_data and roadmap_data.get('content'):
        if not roadmap_data.get('name'):
            roadmap_data['name'] = roadmap_data['content']
    
    # Get max position for new item
    position_result = supabase_admin_client.table('roadmap_items')\
        .select('position')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .order('position', desc=True)\
        .limit(1)\
        .execute()
    
    max_position = 0
    if position_result.data and len(position_result.data) > 0:
        max_position = position_result.data[0].get('position', 0) or 0
    
    # Set position for new item
    roadmap_data['position'] = max_position + 1
    
    # Remove content field as it doesn't exist in the database
    if 'content' in roadmap_data:
        roadmap_data.pop('content')
    
    # Insert roadmap item with user_id
    roadmap_data["user_id"] = user_id
    
    try:
        result = supabase_admin_client.table('roadmap_items').insert(roadmap_data).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create roadmap item"
            )
        
        # Set content field in response to match name
        result.data[0]['content'] = result.data[0].get('name', '')
        
        return result.data[0]
    except Exception as e:
        print(f"Error creating roadmap item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create roadmap item: {str(e)}"
        )


@router.get("/projects/{project_id}/roadmap/{roadmap_id}", response_model=RoadmapItem)
async def get_roadmap_item(
    project_id: str = Path(..., title="The ID of the project"),
    roadmap_id: str = Path(..., title="The ID of the roadmap item"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific roadmap item by ID.
    """
    user_id = current_user["user_id"]
    
    # Query specific roadmap item with RLS filtering by user_id and project_id
    result = supabase_admin_client.table('roadmap_items').select('*')\
        .eq('id', roadmap_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap item not found"
        )
    
    # Map the name field to content for frontend compatibility
    result.data['content'] = result.data.get('name', '')
    
    return result.data


@router.patch("/projects/{project_id}/roadmap/{roadmap_id}", response_model=RoadmapItem)
async def update_roadmap_item(
    roadmap_item_update: RoadmapItemUpdate,
    project_id: str = Path(..., title="The ID of the project"),
    roadmap_id: str = Path(..., title="The ID of the roadmap item"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a specific roadmap item by ID.
    """
    user_id = current_user["user_id"]
    
    # Check if roadmap item exists and belongs to user and project
    check_result = supabase_admin_client.table('roadmap_items').select('id')\
        .eq('id', roadmap_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not check_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap item not found"
        )
    
    # Update roadmap item
    update_data = {k: v for k, v in roadmap_item_update.model_dump().items() if v is not None}
    
    # Handle content/name synchronization - check for content first
    if 'content' in update_data:
        update_data['name'] = update_data['content']
        # Remove content field as it doesn't exist in the database
        update_data.pop('content')
    
    if not update_data:
        # If no fields to update, just return the current roadmap item
        result = supabase_admin_client.table('roadmap_items').select('*')\
            .eq('id', roadmap_id)\
            .single()\
            .execute()
        
        # Ensure content field is set in response
        result.data['content'] = result.data.get('name', '')
        
        return result.data
    
    try:
        result = supabase_admin_client.table('roadmap_items').update(update_data)\
            .eq('id', roadmap_id)\
            .eq('project_id', project_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update roadmap item"
            )
        
        # Set content field to match name in response
        result.data[0]['content'] = result.data[0].get('name', '')
        
        return result.data[0]
    except Exception as e:
        print(f"Error updating roadmap item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update roadmap item: {str(e)}"
        )


@router.delete("/projects/{project_id}/roadmap/{roadmap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_roadmap_item(
    project_id: str = Path(..., title="The ID of the project"),
    roadmap_id: str = Path(..., title="The ID of the roadmap item"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a specific roadmap item by ID.
    """
    user_id = current_user["user_id"]
    
    # Check if roadmap item exists and belongs to user and project
    check_result = supabase_admin_client.table('roadmap_items').select('id')\
        .eq('id', roadmap_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not check_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap item not found"
        )
    
    try:
        # Delete roadmap item
        supabase_admin_client.table('roadmap_items').delete()\
            .eq('id', roadmap_id)\
            .eq('project_id', project_id)\
            .eq('user_id', user_id)\
            .execute()
        
        # No content to return
        return None
    except Exception as e:
        print(f"Error deleting roadmap item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to delete roadmap item: {str(e)}"
        )


@router.put("/projects/{project_id}/roadmap/reorder", response_model=List[RoadmapItem])
async def reorder_roadmap_items(
    reorder_data: RoadmapItemReorder,
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Reorder roadmap items within a category after drag and drop.
    """
    user_id = current_user["user_id"]
    
    # Verify project exists and belongs to user
    project_result = supabase_admin_client.table('projects').select('id')\
        .eq('id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not project_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify all item IDs belong to the user and project
    item_ids = [item_id for item_id in reorder_data.item_ids]
    if not item_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No items to reorder"
        )
    
    # Get all items to verify ownership and update order
    items_result = supabase_admin_client.table('roadmap_items').select('*')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .in_('id', item_ids)\
        .execute()
    
    if not items_result.data or len(items_result.data) != len(item_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more items not found or not owned by user"
        )
    
    # Update each item with its new position
    updated_items = []
    for idx, item_id in enumerate(item_ids):
        update_data = {'position': idx}
        
        # If new category is provided, update the category too
        if reorder_data.new_category:
            update_data['timeframe'] = reorder_data.new_category
        
        # Update the item
        update_result = supabase_admin_client.table('roadmap_items').update(update_data)\
            .eq('id', item_id)\
            .eq('project_id', project_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if update_result.data and len(update_result.data) > 0:
            # Add content field for frontend compatibility
            update_result.data[0]['content'] = update_result.data[0].get('name', '')
            updated_items.append(update_result.data[0])
    
    return updated_items