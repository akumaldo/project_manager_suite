from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Dict, Any, List

from schemas.personas import (
    Persona, PersonaCreate, PersonaUpdate, PersonaList, 
    PersonaDetail, PersonaDetailCreate, PersonaDetailUpdate, PersonaDetailList,
    PersonaDetailCategory, PersonaDetailReorder
)
from auth import get_current_user
from supabase_client import supabase_admin_client

router = APIRouter()


# Persona endpoints

@router.get("/projects/{project_id}/personas", response_model=PersonaList)
async def get_personas(
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all personas for a specific project.
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
    
    # Query personas with RLS filtering by user_id and project_id
    try:
        result = supabase_admin_client.table('personas').select('*')\
            .eq('project_id', project_id)\
            .eq('user_id', user_id)\
            .execute()
        
        # Return empty list if no personas found
        return PersonaList(personas=result.data or [])
    except Exception as e:
        print(f"Error fetching personas: {str(e)}")
        # Return empty list on error
        return PersonaList(personas=[])


@router.post("/projects/{project_id}/personas", response_model=Persona, status_code=status.HTTP_201_CREATED)
async def create_persona(
    persona: PersonaCreate,
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new persona for a specific project.
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
    if persona.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID in path must match project ID in request body"
        )
    
    # Insert persona with user_id
    persona_data = persona.model_dump()
    persona_data["user_id"] = user_id
    
    result = supabase_admin_client.table('personas').insert(persona_data).execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create persona"
        )
    
    return result.data[0]


@router.get("/projects/{project_id}/personas/{persona_id}", response_model=Persona)
async def get_persona(
    project_id: str = Path(..., title="The ID of the project"),
    persona_id: str = Path(..., title="The ID of the persona"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific persona by ID.
    """
    user_id = current_user["user_id"]
    
    # Query specific persona with RLS filtering by user_id and project_id
    result = supabase_admin_client.table('personas').select('*')\
        .eq('id', persona_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found"
        )
    
    return result.data


@router.patch("/projects/{project_id}/personas/{persona_id}", response_model=Persona)
async def update_persona(
    persona_update: PersonaUpdate,
    project_id: str = Path(..., title="The ID of the project"),
    persona_id: str = Path(..., title="The ID of the persona"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a specific persona by ID.
    """
    user_id = current_user["user_id"]
    
    # Check if persona exists and belongs to user and project
    check_result = supabase_admin_client.table('personas').select('id')\
        .eq('id', persona_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not check_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found"
        )
    
    # Update persona
    update_data = {k: v for k, v in persona_update.model_dump().items() if v is not None}
    
    if not update_data:
        # If no fields to update, just return the current persona
        result = supabase_admin_client.table('personas').select('*')\
            .eq('id', persona_id)\
            .single()\
            .execute()
        return result.data
    
    result = supabase_admin_client.table('personas').update(update_data)\
        .eq('id', persona_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update persona"
        )
    
    return result.data[0]


@router.delete("/projects/{project_id}/personas/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona(
    project_id: str = Path(..., title="The ID of the project"),
    persona_id: str = Path(..., title="The ID of the persona"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a specific persona by ID.
    """
    user_id = current_user["user_id"]
    
    # Check if persona exists and belongs to user and project
    check_result = supabase_admin_client.table('personas').select('id')\
        .eq('id', persona_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not check_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found"
        )
    
    # Delete all persona details first
    supabase_admin_client.table('persona_details').delete()\
        .eq('persona_id', persona_id)\
        .execute()
    
    # Then delete the persona
    supabase_admin_client.table('personas').delete()\
        .eq('id', persona_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    return None


# Persona Detail endpoints

@router.get("/personas/{persona_id}/details", response_model=PersonaDetailList)
async def get_persona_details(
    persona_id: str = Path(..., title="The ID of the persona"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all details for a specific persona.
    """
    user_id = current_user["user_id"]
    
    # Verify persona exists and belongs to user
    try:
        persona_result = supabase_admin_client.table('personas').select('id')\
            .eq('id', persona_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if not persona_result.data or len(persona_result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona not found"
            )
    except Exception as e:
        print(f"Error checking for existing persona: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found"
        )
    
    # Query persona details with RLS filtering by user_id and persona_id
    try:
        result = supabase_admin_client.table('persona_details').select('*')\
            .eq('persona_id', persona_id)\
            .eq('user_id', user_id)\
            .order('order_index', desc=False)\
            .execute()
        
        # Return empty list if no details found
        return PersonaDetailList(details=result.data or [])
    except Exception as e:
        print(f"Error fetching persona details: {str(e)}")
        # Return empty list on error
        return PersonaDetailList(details=[])


@router.post("/personas/{persona_id}/details", response_model=PersonaDetail, status_code=status.HTTP_201_CREATED)
async def create_persona_detail(
    detail: PersonaDetailCreate,
    persona_id: str = Path(..., title="The ID of the persona"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new detail for a specific persona.
    """
    user_id = current_user["user_id"]
    
    # Verify persona exists and belongs to user
    persona_result = supabase_admin_client.table('personas').select('id')\
        .eq('id', persona_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not persona_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found"
        )
    
    # Ensure persona_id in path matches persona_id in request body
    if detail.persona_id != persona_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Persona ID in path must match persona ID in request body"
        )
    
    # Get current max order_index for this category
    order_result = supabase_admin_client.table('persona_details').select('order_index')\
        .eq('persona_id', persona_id)\
        .eq('category', detail.category)\
        .order('order_index', desc=True)\
        .limit(1)\
        .execute()
    
    next_order = 0
    if order_result.data and len(order_result.data) > 0:
        next_order = order_result.data[0]['order_index'] + 1
    
    # Insert detail with user_id and calculated order_index
    detail_data = detail.model_dump()
    detail_data["user_id"] = user_id
    detail_data["order_index"] = next_order
    
    result = supabase_admin_client.table('persona_details').insert(detail_data).execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create persona detail"
        )
    
    return result.data[0]


@router.patch("/personas/{persona_id}/details/{detail_id}", response_model=PersonaDetail)
async def update_persona_detail(
    detail_update: PersonaDetailUpdate,
    persona_id: str = Path(..., title="The ID of the persona"),
    detail_id: str = Path(..., title="The ID of the persona detail"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a specific persona detail by ID.
    """
    user_id = current_user["user_id"]
    
    # Check if detail exists and belongs to user and persona
    check_result = supabase_admin_client.table('persona_details').select('id')\
        .eq('id', detail_id)\
        .eq('persona_id', persona_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not check_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona detail not found"
        )
    
    # Update detail
    update_data = {k: v for k, v in detail_update.model_dump().items() if v is not None}
    
    if not update_data:
        # If no fields to update, just return the current detail
        result = supabase_admin_client.table('persona_details').select('*')\
            .eq('id', detail_id)\
            .single()\
            .execute()
        return result.data
    
    result = supabase_admin_client.table('persona_details').update(update_data)\
        .eq('id', detail_id)\
        .eq('persona_id', persona_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update persona detail"
        )
    
    return result.data[0]


@router.delete("/personas/{persona_id}/details/{detail_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona_detail(
    persona_id: str = Path(..., title="The ID of the persona"),
    detail_id: str = Path(..., title="The ID of the persona detail"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a specific persona detail by ID.
    """
    user_id = current_user["user_id"]
    
    # Check if detail exists and belongs to user and persona
    check_result = supabase_admin_client.table('persona_details').select('id')\
        .eq('id', detail_id)\
        .eq('persona_id', persona_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not check_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona detail not found"
        )
    
    # Delete the detail
    supabase_admin_client.table('persona_details').delete()\
        .eq('id', detail_id)\
        .eq('persona_id', persona_id)\
        .eq('user_id', user_id)\
        .execute()
    
    return None


@router.put("/personas/{persona_id}/details/reorder", response_model=List[PersonaDetail])
async def reorder_persona_details(
    reorder_data: PersonaDetailReorder,
    persona_id: str = Path(..., title="The ID of the persona"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Reorder persona details using drag and drop.
    """
    user_id = current_user["user_id"]
    
    # Verify persona exists and belongs to user
    persona_result = supabase_admin_client.table('personas').select('id')\
        .eq('id', persona_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not persona_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona not found"
        )
    
    # Check if all detail IDs exist and belong to this persona and user
    # Also fetch the current category for each item
    updated_items = []
    
    for index, item_id in enumerate(reorder_data.item_ids):
        # Get current item to check ownership and verify it exists
        item_result = supabase_admin_client.table('persona_details').select('*')\
            .eq('id', item_id)\
            .eq('user_id', user_id)\
            .single()\
            .execute()
        
        if not item_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Detail item with ID {item_id} not found or does not belong to user"
            )
        
        # Prepare update data
        update_data = {"order_index": index}
        
        # If new category is provided, update it as well
        if reorder_data.new_category:
            update_data["category"] = reorder_data.new_category
        
        # Update the item
        result = supabase_admin_client.table('persona_details').update(update_data)\
            .eq('id', item_id)\
            .eq('user_id', user_id)\
            .execute()
        
        if result.data and len(result.data) > 0:
            updated_items.append(result.data[0])
    
    return updated_items 