from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Dict, Any, List
import random
from datetime import datetime

from schemas.rice import RICEItem, RICEItemCreate, RICEItemUpdate, RICEItemList
from auth import get_current_user
from supabase_client import supabase_admin_client
from services.ai_service import generate_rice_suggestions as ai_generate_rice_suggestions

router = APIRouter()


@router.get("/projects/{project_id}/rice", response_model=RICEItemList)
async def get_rice_items(
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all RICE items for a specific project.
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
    
    # Query RICE items with RLS filtering by user_id and project_id
    result = supabase_admin_client.table('rice_items').select('*')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .order('rice_score', desc=True)\
        .execute()
    
    if result.data is None:
        return RICEItemList(items=[])
    
    return RICEItemList(items=result.data)


@router.post("/projects/{project_id}/rice", response_model=RICEItem, status_code=status.HTTP_201_CREATED)
async def create_rice_item(
    rice_item: RICEItemCreate,
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new RICE item for a specific project.
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
    if rice_item.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID in path must match project ID in request body"
        )
    
    # Insert RICE item with user_id
    rice_data = rice_item.model_dump()
    rice_data["user_id"] = user_id
    
    # Calculate rice_score
    rice_score = (rice_data['reach_score'] * rice_data['impact_score'] * 
                 rice_data['confidence_score']) / max(1, rice_data['effort_score'])
    
    rice_data["rice_score"] = rice_score
    
    result = supabase_admin_client.table('rice_items').insert(rice_data).execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create RICE item"
        )
    
    return result.data[0]


@router.get("/projects/{project_id}/rice/{rice_id}", response_model=RICEItem)
async def get_rice_item(
    project_id: str = Path(..., title="The ID of the project"),
    rice_id: str = Path(..., title="The ID of the RICE item"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific RICE item by ID.
    """
    user_id = current_user["user_id"]
    
    # Query specific RICE item with RLS filtering by user_id and project_id
    result = supabase_admin_client.table('rice_items').select('*')\
        .eq('id', rice_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RICE item not found"
        )
    
    return result.data


@router.patch("/projects/{project_id}/rice/{rice_id}", response_model=RICEItem)
async def update_rice_item(
    rice_item_update: RICEItemUpdate,
    project_id: str = Path(..., title="The ID of the project"),
    rice_id: str = Path(..., title="The ID of the RICE item"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a specific RICE item by ID.
    """
    user_id = current_user["user_id"]
    
    # Check if RICE item exists and belongs to user and project
    rice_result = supabase_admin_client.table('rice_items').select('*')\
        .eq('id', rice_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not rice_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RICE item not found"
        )
    
    # Update RICE item
    update_data = {k: v for k, v in rice_item_update.model_dump().items() if v is not None}
    
    if not update_data:
        # If no fields to update, just return the current RICE item
        return rice_result.data
    
    # If any score fields are updated, recalculate the RICE score
    score_fields = {'reach_score', 'impact_score', 'confidence_score', 'effort_score'}
    if any(field in update_data for field in score_fields):
        # Get current values for fields not being updated
        current_rice = rice_result.data
        
        # Update with new values
        reach = update_data.get('reach_score', current_rice['reach_score'])
        impact = update_data.get('impact_score', current_rice['impact_score']) 
        confidence = update_data.get('confidence_score', current_rice['confidence_score'])
        effort = update_data.get('effort_score', current_rice['effort_score'])
        
        # Calculate new RICE score
        rice_score = (reach * impact * confidence) / max(1, effort)
        update_data["rice_score"] = rice_score
    
    result = supabase_admin_client.table('rice_items').update(update_data)\
        .eq('id', rice_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update RICE item"
        )
    
    return result.data[0]


@router.delete("/projects/{project_id}/rice/{rice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rice_item(
    project_id: str = Path(..., title="The ID of the project"),
    rice_id: str = Path(..., title="The ID of the RICE item"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a specific RICE item by ID.
    """
    user_id = current_user["user_id"]
    
    # Check if RICE item exists and belongs to user and project
    check_result = supabase_admin_client.table('rice_items').select('id')\
        .eq('id', rice_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not check_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RICE item not found"
        )
    
    # Delete RICE item
    supabase_admin_client.table('rice_items').delete()\
        .eq('id', rice_id)\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    # No content to return
    return None


@router.post("/projects/{project_id}/generate_rice", response_model=Dict[str, List[Dict]])
async def generate_rice_suggestions(
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate AI suggestions for RICE items for a project.
    """
    user_id = current_user["user_id"]
    
    # Verify project exists and belongs to user
    project_result = supabase_admin_client.table('projects').select('id, name, description')\
        .eq('id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not project_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project_name = project_result.data.get('name', 'Unnamed Project')
    project_description = project_result.data.get('description', '')
    
    # Get existing RICE items to avoid duplicates
    rice_items_result = supabase_admin_client.table('rice_items').select('name')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    existing_items = [item['name'] for item in rice_items_result.data] if rice_items_result.data else []
    
    # Generate AI suggestions using the AI service
    try:
        ai_suggestions = await ai_generate_rice_suggestions(
            project_name=project_name,
            context=project_description,
            current_items=existing_items
        )
        
        # Convert AI suggestions to the format expected by the frontend
        suggested_features = []
        
        for suggestion in ai_suggestions:
            # Create a feature with the suggested values and temporary ID
            feature = {
                "id": f"temp-{datetime.now().timestamp()}-{len(suggested_features)}",
                "project_id": project_id,
                "user_id": user_id,
                "name": suggestion.get("name", "Unnamed Feature"),
                "description": suggestion.get("description", ""),
                "reach_score": suggestion.get("reach_score", 5),
                "impact_score": suggestion.get("impact_score", 5),
                "confidence_score": suggestion.get("confidence_score", 5),
                "effort_score": max(1, suggestion.get("effort_score", 5)),  # Ensure effort is at least 1
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Calculate RICE score
            feature["rice_score"] = (
                feature["reach_score"] * 
                feature["impact_score"] * 
                feature["confidence_score"]
            ) / max(1, feature["effort_score"])
            
            suggested_features.append(feature)
        
        return {"suggestions": suggested_features}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate suggestions: {str(e)}"
        ) 