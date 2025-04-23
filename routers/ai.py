from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Dict, Any, List
import uuid
from datetime import datetime
import logging

from schemas.ai import AIPrompt, AISuggestion, AIPromptType
from schemas.csd import CSDCategory
from auth import get_current_user
from supabase_client import supabase_admin_client
from services import ai_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ai/suggest", response_model=AISuggestion)
async def get_ai_suggestions(
    prompt: AIPrompt,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get AI-generated suggestions based on the prompt type.
    """
    user_id = current_user["user_id"]
    
    # Verify project exists and belongs to user
    project_result = supabase_admin_client.table('projects').select('*')\
        .eq('id', prompt.project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not project_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project_name = project_result.data.get('name', 'Unknown Project')
    
    try:
        if prompt.prompt_type == AIPromptType.CSD:
            if not prompt.category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category is required for CSD suggestions"
                )
            
            # Get existing CSD items for context
            existing_items_result = supabase_admin_client.table('csd_items').select('text')\
                .eq('project_id', prompt.project_id)\
                .eq('user_id', user_id)\
                .eq('category', prompt.category)\
                .execute()
            
            existing_items = [item['text'] for item in existing_items_result.data] if existing_items_result.data else []
            
            suggestions = await ai_service.generate_csd_suggestions(
                project_name=project_name,
                category=prompt.category,
                context=prompt.context,
                current_items=existing_items
            )
            
            return AISuggestion(
                suggestions=suggestions,
                reasoning="Generated based on project context and existing CSD items."
            )
            
        elif prompt.prompt_type == AIPromptType.PVB:
            if not prompt.specific_query:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Section name is required for PVB suggestions"
                )
            
            suggestions = await ai_service.generate_pvb_suggestions(
                project_name=project_name,
                section=prompt.specific_query,
                context=prompt.context
            )
            
            return AISuggestion(
                suggestions=suggestions,
                reasoning=f"Generated based on project context for the {prompt.specific_query} section."
            )
            
        elif prompt.prompt_type == AIPromptType.BMC:
            if not prompt.specific_query:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Section name is required for BMC suggestions"
                )
            
            suggestions = await ai_service.generate_bmc_suggestions(
                project_name=project_name,
                section=prompt.specific_query,
                context=prompt.context
            )
            
            return AISuggestion(
                suggestions=suggestions,
                reasoning=f"Generated based on project context for the {prompt.specific_query} section."
            )
            
        elif prompt.prompt_type == AIPromptType.ROADMAP:
            if not prompt.specific_query:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category is required for roadmap suggestions"
                )
            
            # Get existing roadmap items for context
            existing_items_result = supabase_admin_client.table('roadmap_items').select('name')\
                .eq('project_id', prompt.project_id)\
                .eq('user_id', user_id)\
                .execute()
            
            existing_items = [item['name'] for item in existing_items_result.data] if existing_items_result.data else []
            
            # Generate roadmap suggestions
            try:
                suggestions = await ai_service.generate_roadmap_suggestions(
                    project_name=project_name,
                    category=prompt.specific_query,
                    context=prompt.context,
                    current_items=existing_items
                )
                
                return AISuggestion(
                    suggestions=suggestions,
                    reasoning=f"Generated roadmap suggestions for {prompt.specific_query} based on project context."
                )
            except Exception as e:
                logger.error(f"Error generating roadmap suggestions: {str(e)}")
                # Fallback to simple suggestions
                fallback_suggestions = [
                    f"Implement core {prompt.specific_query} features for {project_name}",
                    f"Research {prompt.specific_query} market trends for {project_name}",
                    f"Create {prompt.specific_query} prototypes for {project_name}"
                ]
                return AISuggestion(
                    suggestions=fallback_suggestions,
                    reasoning="Generated using fallback mechanism due to AI service error."
                )
            
        elif prompt.prompt_type == AIPromptType.OKR:
            if prompt.specific_query == "objective":
                suggestions = await ai_service.generate_okr_objective_suggestions(
                    project_name=project_name,
                    context=prompt.context
                )
                
                return AISuggestion(
                    suggestions=suggestions,
                    reasoning="Generated objective suggestions based on project context."
                )
                
            elif prompt.specific_query and prompt.specific_query.startswith("keyresult:"):
                # Format should be "keyresult:objective_text"
                objective_text = prompt.specific_query.replace("keyresult:", "", 1).strip()
                
                if not objective_text:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Objective text is required for key result suggestions"
                    )
                
                suggestions = await ai_service.generate_okr_key_result_suggestions(
                    objective=objective_text,
                    project_name=project_name,
                    context=prompt.context
                )
                
                return AISuggestion(
                    suggestions=suggestions,
                    reasoning="Generated key result suggestions based on the objective."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid specific_query for OKR prompt"
                )
        
        elif prompt.prompt_type == AIPromptType.PERSONA:
            if not prompt.category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category is required for persona suggestions"
                )
                
            suggestions = await ai_service.generate_persona_suggestions(
                project_name=project_name,
                category=prompt.category,
                context=prompt.context
            )
            
            return AISuggestion(
                suggestions=suggestions,
                reasoning=f"Generated {prompt.category.lower()} suggestions for user persona in {project_name}."
            )
        
        else:
            # Handle other prompt types
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Prompt type {prompt.prompt_type} not supported yet"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI suggestions: {str(e)}"
        )

@router.post("/ai/roadmap-suggestions", response_model=Dict[str, List[Dict[str, Any]]])
async def generate_roadmap_suggestions(
    request_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Generate AI suggestions for roadmap items"""
    user_id = current_user["user_id"]
    project_id = request_data.get("project_id")
    category = request_data.get("category")
    view_mode = request_data.get("view_mode")
    
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project ID is required"
        )
    
    # Verify project exists and belongs to user
    project_result = supabase_admin_client.table('projects').select('*')\
        .eq('id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not project_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project = project_result.data
    
    # Get existing project data to provide context
    context_data = {}
    
    # Get BMC data
    bmc_result = supabase_admin_client.table('business_model_canvases').select('*')\
        .eq('project_id', project_id)\
        .single()\
        .execute()
    
    if bmc_result.data:
        context_data["bmc"] = bmc_result.data
    
    # Get existing roadmap items
    roadmap_result = supabase_admin_client.table('roadmap_items').select('*')\
        .eq('project_id', project_id)\
        .execute()
    
    if roadmap_result.data:
        context_data["existing_roadmap"] = roadmap_result.data
    
    # Generate mock suggestions based on the context data
    try:
        # Use mock data for suggestions
        mock_suggestions = []
        
        # Create suggestions based on context
        common_themes = [
            "Implement user authentication",
            "Add analytics dashboard",
            "Create mobile responsive design",
            "Improve search functionality",
            "Add export to PDF feature",
            "Implement dark mode",
            "Create onboarding tutorial",
            "Optimize database queries",
            "Add collaborative editing"
        ]

        # Extract some meaningful context
        project_name = project.get("name", "")
        has_bmc = bool(context_data.get("bmc"))
        roadmap_count = len(context_data.get("existing_roadmap", []))
        
        # Create UUID for each suggestion
        for i in range(3):
            suggestion_id = str(uuid.uuid4())
            # Use the index to get different content for each suggestion
            content_index = (i + roadmap_count) % len(common_themes)
            content = f"{common_themes[content_index]} for {project_name}" if project_name else common_themes[content_index]
            
            if view_mode == "timeframe":
                mock_suggestions.append({
                    "id": suggestion_id,
                    "project_id": project_id,
                    "user_id": user_id,
                    "content": content,
                    "name": content,
                    "description": f"Mock suggestion for {category} timeframe",
                    "timeframe": category,
                    "priority": "medium",
                    "quarter": "Q1",
                    "year": datetime.now().year,
                    "status": "Planned"
                })
            else:
                mock_suggestions.append({
                    "id": suggestion_id,
                    "project_id": project_id,
                    "user_id": user_id,
                    "content": content,
                    "name": content,
                    "description": f"Mock suggestion with {category} priority",
                    "timeframe": "next",
                    "priority": category,
                    "quarter": "Q1",
                    "year": datetime.now().year,
                    "status": "Planned"
                })
        
        return {"suggestions": mock_suggestions}
    
    except Exception as e:
        logger.error(f"Error generating AI suggestions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI suggestions: {str(e)}"
        ) 