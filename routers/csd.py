from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Dict, Any, List

from schemas.csd import CSDItem, CSDItemCreate, CSDItemUpdate, CSDItemList, CSDCategory, CSDItemReorder
from auth import get_current_user
from supabase_client import supabase_admin_client

router = APIRouter()


@router.get("/projects/{project_id}/csd_items", response_model=CSDItemList)
async def get_csd_items(
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all CSD items for a specific project.
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
    
    # Query CSD items with RLS filtering by user_id and project_id
    try:
        result = supabase_admin_client.table('csd_items').select('*')\
            .eq('project_id', project_id)\
            .eq('user_id', user_id)\
            .execute()
        
        # Return empty list if no items found
        return CSDItemList(items=result.data or [])
    except Exception as e:
        print(f"Error fetching CSD items: {str(e)}")
        # Return empty list on error
        return CSDItemList(items=[])


@router.post("/projects/{project_id}/csd", response_model=CSDItem, status_code=status.HTTP_201_CREATED)
async def create_csd_item(
    csd_item: CSDItemCreate,
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new CSD item for a specific project.
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
    if csd_item.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID in path must match project ID in request body"
        )
    
    # Insert CSD item with user_id
    csd_data = csd_item.model_dump()
    csd_data["user_id"] = user_id
    
    result = supabase_admin_client.table('csd_items').insert(csd_data).execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create CSD item"
        )
    
    return result.data[0]


@router.get("/projects/{project_id}/csd/{csd_id}", response_model=CSDItem)
async def get_csd_item(
    project_id: str = Path(..., title="The ID of the project"),
    csd_id: str = Path(..., title="The ID of the CSD item"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific CSD item by ID.
    """
    user_id = current_user["user_id"]
    
    # Query specific CSD item with RLS filtering by user_id and project_id
    result = supabase_admin_client.table('csd_items').select('*')\
        .eq('id', csd_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSD item not found"
        )
    
    return result.data


@router.patch("/projects/{project_id}/csd/{csd_id}", response_model=CSDItem)
async def update_csd_item(
    csd_item_update: CSDItemUpdate,
    project_id: str = Path(..., title="The ID of the project"),
    csd_id: str = Path(..., title="The ID of the CSD item"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a specific CSD item by ID.
    """
    user_id = current_user["user_id"]
    
    # Check if CSD item exists and belongs to user and project
    check_result = supabase_admin_client.table('csd_items').select('id')\
        .eq('id', csd_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not check_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSD item not found"
        )
    
    # Update CSD item
    update_data = {k: v for k, v in csd_item_update.model_dump().items() if v is not None}
    
    if not update_data:
        # If no fields to update, just return the current CSD item
        result = supabase_admin_client.table('csd_items').select('*')\
            .eq('id', csd_id)\
            .single()\
            .execute()
        return result.data
    
    result = supabase_admin_client.table('csd_items').update(update_data)\
        .eq('id', csd_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update CSD item"
        )
    
    return result.data[0]


@router.delete("/projects/{project_id}/csd/{csd_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_csd_item(
    project_id: str = Path(..., title="The ID of the project"),
    csd_id: str = Path(..., title="The ID of the CSD item"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a specific CSD item by ID.
    """
    user_id = current_user["user_id"]
    
    # Check if CSD item exists and belongs to user and project
    check_result = supabase_admin_client.table('csd_items').select('id')\
        .eq('id', csd_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not check_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSD item not found"
        )
    
    # Delete CSD item
    supabase_admin_client.table('csd_items').delete()\
        .eq('id', csd_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    # No content to return
    return None


@router.put("/projects/{project_id}/csd/reorder", response_model=List[CSDItem])
async def reorder_csd_items(
    reorder_data: CSDItemReorder,
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Reorder CSD items within a category after drag and drop.
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
    items_result = supabase_admin_client.table('csd_items').select('*')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .in_('id', item_ids)\
        .execute()
    
    if not items_result.data or len(items_result.data) != len(item_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more items not found or not owned by user"
        )
    
    # Update each item in the database with its new category if changed
    updated_items = []
    
    for index, item_id in enumerate(item_ids):
        # If category changed, update it
        item_data = next((item for item in items_result.data if item['id'] == item_id), None)
        
        if not item_data:
            continue
            
        update_data = {}
        if reorder_data.new_category and item_data['category'] != reorder_data.new_category:
            update_data['category'] = reorder_data.new_category
            
        # Add any other ordering fields if needed
        # For example, if you want to store the actual order:
        # update_data['order_index'] = index
        
        if update_data:
            result = supabase_admin_client.table('csd_items').update(update_data)\
                .eq('id', item_id)\
                .eq('project_id', project_id)\
                .eq('user_id', user_id)\
                .execute()
                
            if result.data and len(result.data) > 0:
                updated_items.append(result.data[0])
        else:
            updated_items.append(item_data)
    
    return updated_items 