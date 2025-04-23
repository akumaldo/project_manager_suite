from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Dict, Any, List

from schemas.bmc import BMC, BMCCreate, BMCUpdate, BMCItem, BMCItemCreate, BMCItemUpdate
from auth import get_current_user
from supabase_client import supabase_admin_client

router = APIRouter()


@router.get("/projects/{project_id}/bmc", response_model=BMC)
async def get_business_model_canvas(
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the Business Model Canvas for a specific project.
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
    
    # Query BMC with RLS filtering by user_id and project_id
    result = supabase_admin_client.table('business_model_canvases').select('*')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    # If no BMC exists, return a 404
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business Model Canvas not found"
        )
    
    return result.data


@router.post("/projects/{project_id}/bmc", response_model=BMC, status_code=status.HTTP_201_CREATED)
async def create_business_model_canvas(
    bmc: BMCCreate,
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new Business Model Canvas for a specific project.
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
    
    # Check if a BMC already exists for this project
    existing_result = supabase_admin_client.table('business_model_canvases').select('id')\
        .eq('project_id', project_id)\
        .single()\
        .execute()
    
    if existing_result.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A Business Model Canvas already exists for this project"
        )
    
    # Ensure project_id in path matches project_id in request body
    if bmc.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID in path must match project ID in request body"
        )
    
    # Insert BMC with user_id
    bmc_data = bmc.model_dump()
    bmc_data["user_id"] = user_id
    
    result = supabase_admin_client.table('business_model_canvases').insert(bmc_data).execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Business Model Canvas"
        )
    
    return result.data[0]


@router.patch("/projects/{project_id}/bmc", response_model=BMC)
async def update_business_model_canvas(
    bmc_update: BMCUpdate,
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update the Business Model Canvas for a specific project.
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
    
    # Check if BMC exists and belongs to user and project
    bmc_result = supabase_admin_client.table('business_model_canvases').select('id')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not bmc_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business Model Canvas not found"
        )
    
    # Update fields that are not None
    update_data = {k: v for k, v in bmc_update.model_dump().items() if v is not None}
    
    if not update_data:
        # If no fields to update, just return the current BMC
        result = supabase_admin_client.table('business_model_canvases').select('*')\
            .eq('project_id', project_id)\
            .eq('user_id', user_id)\
            .single()\
            .execute()
        return result.data
    
    # Update BMC
    result = supabase_admin_client.table('business_model_canvases').update(update_data)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update Business Model Canvas"
        )
    
    return result.data[0]


# BMC Items endpoints
@router.get("/projects/{project_id}/bmc-items", response_model=List[BMCItem])
async def get_bmc_items(
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all BMC items for a specific project.
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
    
    # Query BMC items
    result = supabase_admin_client.table('bmc_items').select('*')\
        .eq('project_id', project_id)\
        .order('position', desc=False)\
        .execute()
    
    return result.data

@router.post("/projects/{project_id}/bmc-items", response_model=BMCItem, status_code=status.HTTP_201_CREATED)
async def create_bmc_item(
    item: BMCItemCreate,
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new BMC item for a specific project.
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
    
    # Prepare item data
    item_data = item.model_dump()
    item_data["project_id"] = project_id
    item_data["user_id"] = user_id
    
    # Get current max position for the block
    position_result = supabase_admin_client.table('bmc_items').select('position')\
        .eq('project_id', project_id)\
        .eq('block', item.block)\
        .order('position', desc=True)\
        .limit(1)\
        .execute()
    
    # Set position as max + 1 or 0 if no items exist
    if position_result.data and len(position_result.data) > 0:
        item_data["position"] = position_result.data[0]["position"] + 1
    else:
        item_data["position"] = 0
    
    # Insert the item
    result = supabase_admin_client.table('bmc_items').insert(item_data).execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create BMC item"
        )
    
    return result.data[0]

@router.patch("/projects/{project_id}/bmc-items/{item_id}", response_model=BMCItem)
async def update_bmc_item(
    item_update: BMCItemUpdate,
    project_id: str = Path(..., title="The ID of the project"),
    item_id: str = Path(..., title="The ID of the BMC item"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a BMC item.
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
    
    # Verify item exists and belongs to project
    item_result = supabase_admin_client.table('bmc_items').select('id')\
        .eq('id', item_id)\
        .eq('project_id', project_id)\
        .single()\
        .execute()
    
    if not item_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BMC item not found"
        )
    
    # Update fields that are not None
    update_data = {k: v for k, v in item_update.model_dump().items() if v is not None}
    
    if not update_data:
        # If no fields to update, just return the current item
        result = supabase_admin_client.table('bmc_items').select('*')\
            .eq('id', item_id)\
            .single()\
            .execute()
        return result.data
    
    # Update item
    result = supabase_admin_client.table('bmc_items').update(update_data)\
        .eq('id', item_id)\
        .execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update BMC item"
        )
    
    return result.data[0]

@router.delete("/projects/{project_id}/bmc-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bmc_item(
    project_id: str = Path(..., title="The ID of the project"),
    item_id: str = Path(..., title="The ID of the BMC item"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a BMC item.
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
    
    # Verify item exists and belongs to project
    item_result = supabase_admin_client.table('bmc_items').select('id')\
        .eq('id', item_id)\
        .eq('project_id', project_id)\
        .single()\
        .execute()
    
    if not item_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BMC item not found"
        )
    
    # Delete the item
    supabase_admin_client.table('bmc_items').delete()\
        .eq('id', item_id)\
        .execute()
    
    return None 