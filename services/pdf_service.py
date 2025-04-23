import os
import asyncio
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

from config import settings
from supabase_client import supabase_admin_client


def html_to_pdf(html_content: str) -> io.BytesIO:
    """
    Convert HTML content to PDF using xhtml2pdf.
    
    Args:
        html_content: HTML string to convert
        
    Returns:
        BytesIO object containing the PDF
    """
    pdf_buffer = io.BytesIO()
    
    # Convert HTML to PDF
    pisa_status = pisa.CreatePDF(
        html_content,
        dest=pdf_buffer
    )
    
    # Check if conversion was successful
    if pisa_status.err:
        raise Exception(f"HTML to PDF conversion failed: {pisa_status.err}")
    
    # Reset the buffer position to the beginning
    pdf_buffer.seek(0)
    return pdf_buffer


async def fetch_project_data(project_id: str, user_id: str) -> Dict[str, Any]:
    """
    Fetch all required project data from Supabase for the report.
    
    Args:
        project_id: The ID of the project
        user_id: The ID of the user
        
    Returns:
        Dictionary containing all project data
    """
    # Fetch project details
    project_result = supabase_admin_client.table('projects').select('*')\
        .eq('id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    if not project_result.data:
        raise Exception("Project not found")
    
    project = project_result.data
    
    # Fetch all data concurrently
    csd_result = supabase_admin_client.table('csd_items').select('*')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    pvb_result = supabase_admin_client.table('product_vision_boards').select('*')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    bmc_result = supabase_admin_client.table('business_model_canvases').select('*')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    rice_result = supabase_admin_client.table('rice_items').select('*')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .order('rice_score', desc=True)\
        .execute()
    
    roadmap_result = supabase_admin_client.table('roadmap_items').select('*')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .order('year', desc=False)\
        .order('quarter', desc=False)\
        .execute()
    
    objectives_result = supabase_admin_client.table('objectives').select('*')\
        .eq('project_id', project_id)\
        .eq('user_id', user_id)\
        .execute()
    
    # Organize CSD items by category
    csd_items = {
        "Certainty": [],
        "Supposition": [],
        "Doubt": []
    }
    
    if csd_result.data:
        for item in csd_result.data:
            category = item.get('category')
            if category in csd_items:
                csd_items[category].append(item)
    
    # Get key results for each objective
    objectives_with_key_results = []
    
    if objectives_result.data:
        for objective in objectives_result.data:
            key_results_result = supabase_admin_client.table('key_results').select('*')\
                .eq('objective_id', objective['id'])\
                .execute()
            
            key_results = key_results_result.data if key_results_result.data else []
            
            # Calculate progress for objective based on key results
            if key_results:
                total_progress = sum(kr.get('current_value', 0) / kr.get('target_value', 1) * 100 for kr in key_results)
                objective_progress = total_progress / len(key_results)
            else:
                objective_progress = 0
            
            objectives_with_key_results.append({
                "objective": objective,
                "key_results": key_results,
                "progress": round(objective_progress, 1)
            })
    
    # Assemble and return the data
    return {
        "project": project,
        "csd": csd_items,
        "pvb": pvb_result.data if pvb_result.data else None,
        "bmc": bmc_result.data if bmc_result.data else None,
        "rice": rice_result.data if rice_result.data else [],
        "roadmap": roadmap_result.data if roadmap_result.data else [],
        "okr": objectives_with_key_results,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


async def generate_pdf_report(
    project_id: str,
    user_id: str,
    frameworks: List[str],
    include_cover_page: bool = True,
    include_toc: bool = True
) -> io.BytesIO:
    """
    Generate a PDF report for a project with selected frameworks.
    
    Args:
        project_id: The ID of the project
        user_id: The ID of the user
        frameworks: List of frameworks to include
        include_cover_page: Whether to include a cover page
        include_toc: Whether to include a table of contents
        
    Returns:
        BytesIO object containing the PDF
    """
    # Get project data
    project_data = await fetch_project_data(project_id, user_id)
    
    # Set up Jinja2 templates
    templates_dir = Path(settings.pdf_report_template_path).parent
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template(Path(settings.pdf_report_template_path).name)
    
    # Render the template with the project data
    html_content = template.render(
        project=project_data["project"],
        csd=project_data["csd"],
        pvb=project_data["pvb"],
        bmc=project_data["bmc"],
        rice=project_data["rice"],
        roadmap=project_data["roadmap"],
        okr=project_data["okr"],
        frameworks=frameworks,
        include_cover_page=include_cover_page,
        include_toc=include_toc,
        generated_at=project_data["generated_at"]
    )
    
    # Generate the PDF
    return html_to_pdf(html_content) 