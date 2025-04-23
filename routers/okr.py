from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Dict, Any, List

from schemas.okr import (
    Objective, ObjectiveCreate, ObjectiveUpdate, 
    KeyResult, KeyResultCreate, KeyResultUpdate,
    ObjectiveWithKeyResults, ObjectiveList
)
from auth import get_current_user
from supabase_client import supabase_admin_client

router = APIRouter()


@router.get("/projects/{project_id}/okr", response_model=ObjectiveList)
async def get_objectives(
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all objectives with their key results for a specific project.
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
    
    # Query objectives with RLS filtering by user_id and project_id
    objectives_result = supabase_admin_client.table('objectives').select('*')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not objectives_result.data:
        return ObjectiveList(objectives=[])
    
    objectives_with_key_results = []
    
    # For each objective, fetch its key results
    for objective in objectives_result.data:
        key_results_result = supabase_admin_client.table('key_results').select('*')\
            .eq('objective_id', objective['id'])\
            .execute()
        
        key_results = key_results_result.data if key_results_result.data else []
        
        objective_with_kr = ObjectiveWithKeyResults(
            **objective,
            key_results=key_results
        )
        objectives_with_key_results.append(objective_with_kr)
    
    return ObjectiveList(objectives=objectives_with_key_results)


@router.post("/projects/{project_id}/okr/objectives", response_model=Objective, status_code=status.HTTP_201_CREATED)
async def create_objective(
    objective: ObjectiveCreate,
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new objective for a specific project.
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
    if objective.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID in path must match project ID in request body"
        )
    
    # Insert objective with user_id
    objective_data = objective.model_dump()
    objective_data["user_id"] = user_id
    
    result = supabase_admin_client.table('objectives').insert(objective_data).execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create objective"
        )
    
    return result.data[0]


@router.post("/projects/{project_id}/okr/objectives/{objective_id}/key-results", 
           response_model=KeyResult, 
           status_code=status.HTTP_201_CREATED)
async def create_key_result(
    key_result: KeyResultCreate,
    project_id: str = Path(..., title="The ID of the project"),
    objective_id: str = Path(..., title="The ID of the objective"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new key result for a specific objective.
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
    
    # Verify objective exists, belongs to the project, and the user
    objective_result = supabase_admin_client.table('objectives').select('id')\
        .eq('id', objective_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not objective_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objective not found"
        )
    
    # Ensure objective_id in path matches objective_id in request body
    if key_result.objective_id != objective_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Objective ID in path must match objective ID in request body"
        )
    
    # Insert key result
    key_result_data = key_result.model_dump()
    
    result = supabase_admin_client.table('key_results').insert(key_result_data).execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create key result"
        )
    
    return result.data[0]


@router.patch("/projects/{project_id}/okr/objectives/{objective_id}", response_model=Objective)
async def update_objective(
    objective_update: ObjectiveUpdate,
    project_id: str = Path(..., title="The ID of the project"),
    objective_id: str = Path(..., title="The ID of the objective"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a specific objective by ID.
    """
    user_id = current_user["user_id"]
    
    # Check if objective exists and belongs to user and project
    check_result = supabase_admin_client.table('objectives').select('id')\
        .eq('id', objective_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not check_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objective not found"
        )
    
    # Update objective
    update_data = {k: v for k, v in objective_update.model_dump().items() if v is not None}
    
    if not update_data:
        # If no fields to update, just return the current objective
        result = supabase_admin_client.table('objectives').select('*')\
            .eq('id', objective_id)\
            .single()\
            .execute()
        return result.data
    
    result = supabase_admin_client.table('objectives').update(update_data)\
        .eq('id', objective_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update objective"
        )
    
    return result.data[0]


@router.patch("/projects/{project_id}/okr/key-results/{key_result_id}", response_model=KeyResult)
async def update_key_result(
    key_result_update: KeyResultUpdate,
    project_id: str = Path(..., title="The ID of the project"),
    key_result_id: str = Path(..., title="The ID of the key result"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a specific key result by ID.
    """
    user_id = current_user["user_id"]
    
    # First, verify the project exists and belongs to the user
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
    
    # Get the key result
    kr_result = supabase_admin_client.table('key_results').select('*')\
        .eq('id', key_result_id)\
        .single()\
        .execute()
    
    if not kr_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key result not found"
        )
    
    # Verify the key result belongs to an objective that belongs to the project
    objective_id = kr_result.data['objective_id']
    
    objective_result = supabase_admin_client.table('objectives').select('id')\
        .eq('id', objective_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not objective_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key result does not belong to this project"
        )
    
    # Update key result
    update_data = {k: v for k, v in key_result_update.model_dump().items() if v is not None}
    
    if not update_data:
        # If no fields to update, just return the current key result
        return kr_result.data
    
    result = supabase_admin_client.table('key_results').update(update_data)\
        .eq('id', key_result_id)\
        .execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update key result"
        )
    
    return result.data[0]


@router.delete("/projects/{project_id}/okr/objectives/{objective_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_objective(
    project_id: str = Path(..., title="The ID of the project"),
    objective_id: str = Path(..., title="The ID of the objective"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a specific objective by ID and all its key results.
    """
    user_id = current_user["user_id"]
    
    # Check if objective exists and belongs to user and project
    check_result = supabase_admin_client.table('objectives').select('id')\
        .eq('id', objective_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not check_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Objective not found"
        )
    
    # First delete all key results for this objective
    supabase_admin_client.table('key_results').delete()\
        .eq('objective_id', objective_id)\
        .execute()
    
    # Then delete the objective
    supabase_admin_client.table('objectives').delete()\
        .eq('id', objective_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    # No content to return
    return None


@router.delete("/projects/{project_id}/okr/key-results/{key_result_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key_result(
    project_id: str = Path(..., title="The ID of the project"),
    key_result_id: str = Path(..., title="The ID of the key result"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a specific key result by ID.
    """
    user_id = current_user["user_id"]
    
    # First, verify the project exists and belongs to the user
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
    
    # Get the key result
    kr_result = supabase_admin_client.table('key_results').select('*')\
        .eq('id', key_result_id)\
        .single()\
        .execute()
    
    if not kr_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key result not found"
        )
    
    # Verify the key result belongs to an objective that belongs to the project
    objective_id = kr_result.data['objective_id']
    
    objective_result = supabase_admin_client.table('objectives').select('id')\
        .eq('id', objective_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not objective_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Key result does not belong to this project"
        )
    
    # Delete the key result
    supabase_admin_client.table('key_results').delete()\
        .eq('id', key_result_id)\
        .execute()
    
    # No content to return
    return None 