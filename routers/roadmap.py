from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Dict, Any, List

from schemas.roadmap import RoadmapItem, RoadmapItemCreate, RoadmapItemUpdate, RoadmapItemList
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
    
    # Query roadmap items with RLS filtering by user_id and project_id
    result = supabase_admin_client.table('roadmap_items').select('*')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .order('year', desc=False)\
        .order('quarter', desc=False)\
        .execute()
    
    if result.data is None:
        return RoadmapItemList(items=[])
    
    # Process the data to ensure frontend compatibility
    for item in result.data:
        # Map the name field to content for frontend compatibility
        item['content'] = item.get('name', '')
    
    return RoadmapItemList(items=result.data)


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
    
    # If content is provided but name is not, use content as name
    roadmap_data = roadmap_item.model_dump()
    if roadmap_data.get('content') and not roadmap_data.get('name'):
        roadmap_data['name'] = roadmap_data['content']
    
    # Remove content field as it doesn't exist in the database
    if 'content' in roadmap_data:
        roadmap_data.pop('content')
    
    # Insert roadmap item with user_id
    roadmap_data["user_id"] = user_id
    
    try:
        # Use standard Supabase insert method
        result = supabase_admin_client.table('roadmap_items').insert(roadmap_data).execute()
        
        # Make sure we got a result
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create roadmap item"
            )
            
        # Ensure content field is set in response
        result.data[0]['content'] = result.data[0].get('name', '')
        
        return result.data[0]
    except Exception as e:
        # Log the error and provide a helpful message
        import logging
        logging.error(f"Error creating roadmap item: {str(e)}")
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
    # Debug prints to see what data we're receiving
    import logging
    logging.info(f"Received update request for roadmap item {roadmap_id}")
    logging.info(f"Update data (raw): {roadmap_item_update}")
    logging.info(f"Update data (model dump): {roadmap_item_update.model_dump()}")
    
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
    logging.info(f"Filtered update data: {update_data}")
    
    # Handle content/name synchronization - check for content first
    if 'content' in update_data:
        logging.info(f"Content field present: {update_data['content']}")
        update_data['name'] = update_data['content']
        # Remove content field as it doesn't exist in the database
        update_data.pop('content')
    
    # Already has name field, skip content field handling
    logging.info(f"Final update data: {update_data}")
    
    if not update_data:
        logging.warning("No fields to update after processing")
        # If no fields to update, just return the current roadmap item
        result = supabase_admin_client.table('roadmap_items').select('*')\
            .eq('id', roadmap_id)\
            .single()\
            .execute()
        
        # Ensure content field is set in response
        result.data['content'] = result.data.get('name', '')
        logging.info(f"Returning existing data: {result.data}")
        
        return result.data
    
    try:
        # Use standard Supabase update method
        logging.info(f"Sending update to database: {update_data}")
        result = supabase_admin_client.table('roadmap_items').update(update_data)\
            .eq('id', roadmap_id)\
            .eq('project_id', project_id)\
            .eq('user_id', user_id)\
            .execute()
        
        # Make sure we got a result
        if not result.data or len(result.data) == 0:
            logging.error("No data returned from update query")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update roadmap item"
            )
        
        # Set content field to match name in response
        result.data[0]['content'] = result.data[0].get('name', '')
        logging.info(f"Update successful, returning: {result.data[0]}")
        
        return result.data[0]
    except Exception as e:
        # Log the error and provide a helpful message
        logging.error(f"Error updating roadmap item: {str(e)}")
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
        # Use standard Supabase delete method
        supabase_admin_client.table('roadmap_items').delete()\
            .eq('id', roadmap_id)\
            .eq('project_id', project_id)\
            .eq('user_id', user_id)\
            .execute()
        
        # No content to return
        return None
    except Exception as e:
        # Log the error and provide a helpful message
        import logging
        logging.error(f"Error deleting roadmap item: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to delete roadmap item: {str(e)}"
        )