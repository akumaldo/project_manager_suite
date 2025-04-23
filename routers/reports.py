from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List

from schemas.reports import ReportRequest
from auth import get_current_user
from supabase_client import supabase_admin_client
from services import pdf_service

router = APIRouter()


@router.post("/projects/{project_id}/report")
async def generate_report(
    report_request: ReportRequest,
    project_id: str = Path(..., title="The ID of the project"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate a PDF report for a project.
    
    Args:
        report_request: Contains which frameworks to include in the report
        project_id: The ID of the project
        current_user: The authenticated user
        
    Returns:
        A PDF file as a streaming response
    """
    user_id = current_user["user_id"]
    
    # Verify project exists and belongs to user
    project_result = supabase_admin_client.table('projects').select('name')\
        .eq('id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not project_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project_name = project_result.data.get('name', 'Project')
    
    try:
        # Generate the PDF
        pdf_buffer = await pdf_service.generate_pdf_report(
            project_id=project_id,
            user_id=user_id,
            frameworks=[fw.value for fw in report_request.frameworks],
            include_cover_page=report_request.include_cover_page,
            include_toc=report_request.include_toc
        )
        
        # Return the PDF as a streaming response
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{project_name}_Report.pdf"'
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        ) 