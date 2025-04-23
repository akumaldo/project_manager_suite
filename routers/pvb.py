from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Dict, Any

from schemas.pvb import PVB, PVBCreate, PVBUpdate
from auth import get_current_user
from supabase_client import supabase_admin_client

router = APIRouter()


@router.get("/projects/{project_id}/pvb", response_model=PVB)
async def get_product_vision_board(
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the Product Vision Board for a specific project.
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
    
    # Query Product Vision Board with RLS filtering by user_id and project_id
    try:
        # Try to get the PVB, but handle the case where it doesn't exist
        result = supabase_admin_client.table('product_vision_boards').select('*')\
            .eq('project_id', project_id)\
            .eq('user_id', user_id)\
            .execute()
        
        # Check if we actually got data back
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product Vision Board not found"
            )
        
        return result.data[0]
    except Exception as e:
        # Log error for debugging
        print(f"Error fetching PVB: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product Vision Board not found"
        )


@router.post("/projects/{project_id}/pvb", response_model=PVB, status_code=status.HTTP_201_CREATED)
async def create_product_vision_board(
    pvb: PVBCreate,
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new Product Vision Board for a specific project.
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
    
    # Check if a PVB already exists for this project
    try:
        existing_result = supabase_admin_client.table('product_vision_boards').select('id')\
            .eq('project_id', project_id)\
            .execute()
        
        # If we found existing rows, it means a PVB already exists
        if existing_result.data and len(existing_result.data) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A Product Vision Board already exists for this project"
            )
    except Exception as e:
        # Log the error but continue - no existing PVB is what we want
        print(f"Error checking for existing PVB: {str(e)}")
    
    # Ensure project_id in path matches project_id in request body
    if pvb.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID in path must match project ID in request body"
        )
    
    # Insert Product Vision Board with user_id
    pvb_data = pvb.model_dump()
    pvb_data["user_id"] = user_id
    
    result = supabase_admin_client.table('product_vision_boards').insert(pvb_data).execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Product Vision Board"
        )
    
    return result.data[0]


@router.patch("/projects/{project_id}/pvb", response_model=PVB)
async def update_product_vision_board(
    pvb_update: PVBUpdate,
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update the Product Vision Board for a specific project.
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
    
    # Check if PVB exists and belongs to user and project
    try:
        pvb_result = supabase_admin_client.table('product_vision_boards').select('id')\
            .eq('project_id', project_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if not pvb_result.data or len(pvb_result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product Vision Board not found"
            )
        
        pvb_id = pvb_result.data[0]['id']
    except Exception as e:
        print(f"Error checking for existing PVB: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product Vision Board not found"
        )
    
    # Update fields that are not None
    update_data = {k: v for k, v in pvb_update.model_dump().items() if v is not None}
    
    if not update_data:
        # If no fields to update, just return the current PVB
        try:
            result = supabase_admin_client.table('product_vision_boards').select('*')\
                .eq('project_id', project_id)\
                .eq('user_id', user_id)\
                .execute()
                
            if not result.data or len(result.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product Vision Board not found"
                )
                
            return result.data[0]
        except Exception as e:
            print(f"Error fetching current PVB: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product Vision Board not found"
            )
    
    # Update Product Vision Board
    try:
        result = supabase_admin_client.table('product_vision_boards').update(update_data)\
            .eq('project_id', project_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update Product Vision Board"
            )
        
        return result.data[0]
    except Exception as e:
        print(f"Error updating PVB: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update Product Vision Board: {str(e)}"
        ) 