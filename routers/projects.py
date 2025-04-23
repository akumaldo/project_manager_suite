from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List

from schemas.projects import Project, ProjectCreate, ProjectUpdate, ProjectList
from auth import get_current_user
from supabase_client import supabase_admin_client

router = APIRouter()


@router.get("/projects", response_model=ProjectList)
async def get_projects(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all projects for the authenticated user.
    """
    user_id = current_user["user_id"]
    
    # Query projects table with RLS filtering by user_id
    result = supabase_admin_client.table('projects').select('*')\
        .eq('user_id', user_id)\
        .order('updated_at', desc=True)\
        .execute()
    
    if result.data is None:
        return ProjectList(projects=[])
    
    return ProjectList(projects=result.data)


@router.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new project for the authenticated user.
    """
    user_id = current_user["user_id"]
    
    # Insert project with user_id
    project_data = project.model_dump()
    project_data["user_id"] = user_id
    
    result = supabase_admin_client.table('projects').insert(project_data).execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )
    
    return result.data[0]


@router.get("/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific project by ID.
    """
    user_id = current_user["user_id"]
    
    # Query specific project with RLS filtering by user_id
    result = supabase_admin_client.table('projects').select('*')\
        .eq('id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return result.data


@router.patch("/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a specific project by ID.
    """
    user_id = current_user["user_id"]
    
    # First, check if project exists and belongs to user
    check_result = supabase_admin_client.table('projects').select('id')\
        .eq('id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not check_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update project
    update_data = {k: v for k, v in project_update.model_dump().items() if v is not None}
    
    if not update_data:
        # If no fields to update, just return the current project
        result = supabase_admin_client.table('projects').select('*')\
            .eq('id', project_id)\
            .single()\
            .execute()
        return result.data
    
    # Update with timestamp
    result = supabase_admin_client.table('projects').update(update_data)\
        .eq('id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )
    
    return result.data[0]


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a specific project by ID.
    """
    user_id = current_user["user_id"]
    
    # Check if project exists and belongs to user
    check_result = supabase_admin_client.table('projects').select('id')\
        .eq('id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not check_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Delete project
    supabase_admin_client.table('projects').delete()\
        .eq('id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    # No content to return
    return None 