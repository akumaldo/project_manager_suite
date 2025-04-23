import httpx
import json
from typing import List, Dict, Any, Optional

from config import settings


async def generate_ai_suggestions(
    prompt_text: str, 
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Generate suggestions using OpenRouter API with the DeepSeek model.
    
    Args:
        prompt_text: The prompt text to send to the model
        max_tokens: Maximum number of tokens to generate
        temperature: Controls randomness (higher = more creative)
        
    Returns:
        Dictionary containing the suggestion results
    """
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://product-discovery-hub.com"  # replace with your actual domain
    }
    
    payload = {
        "model": settings.openrouter_model,
        "messages": [{"role": "user", "content": prompt_text}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        try:
            content = result["choices"][0]["message"]["content"]
            return {"content": content}
        except (KeyError, IndexError) as e:
            raise Exception(f"Unexpected API response format: {e}")


async def generate_csd_suggestions(
    project_name: str,
    category: str,
    context: Optional[str] = None,
    current_items: Optional[List[str]] = None
) -> List[str]:
    """
    Generate CSD matrix suggestions based on the project and category.
    
    Args:
        project_name: The name of the project
        category: 'Certainty', 'Supposition', or 'Doubt'
        context: Optional additional context about the project
        current_items: Existing items in the CSD matrix
        
    Returns:
        List of suggestions
    """
    existing_items = ""
    if current_items and len(current_items) > 0:
        existing_items = "Existing items in this category:\n" + "\n".join([f"- {item}" for item in current_items])
    
    prompt = f"""
    You are a product discovery expert helping a team with their Certainty-Supposition-Doubt (CSD) Matrix.

    Project: {project_name}
    Category: {category}
    {f'Context: {context}' if context else ''}
    {existing_items}

    Based on the project name and any context provided, please suggest 3-5 concise, clear, and insightful items for the {category} category of the CSD Matrix.

    Certainties = What we know for sure
    Suppositions = What we believe but aren't certain about
    Doubts = What we're unsure about and need to investigate

    Return ONLY the suggestions, one per line, with no numbering, headers, or other text.
    """
    
    result = await generate_ai_suggestions(prompt)
    
    # Parse the response - split by newlines and clean up
    suggestions = [line.strip() for line in result["content"].split("\n") if line.strip()]
    
    # Remove any bullet points or numbering
    suggestions = [s.lstrip("- ").lstrip("* ").lstrip("1234567890). ") for s in suggestions]
    
    return suggestions


async def generate_pvb_suggestions(
    project_name: str,
    section: str,
    context: Optional[str] = None
) -> List[str]:
    """
    Generate Product Vision Board suggestions based on the project and section.
    
    Args:
        project_name: The name of the project
        section: The PVB section (vision, target_customers, customer_needs, 
                 product_features, business_goals)
        context: Optional additional context about the project
        
    Returns:
        List of suggestions
    """
    # Map section names to user-friendly names
    section_names = {
        "vision": "Vision Statement",
        "target_customers": "Target Customers",
        "customer_needs": "Customer Needs/Problems",
        "product_features": "Product Features",
        "business_goals": "Business Goals"
    }
    
    section_display = section_names.get(section, section.replace("_", " ").title())
    
    prompt = f"""
    You are a product strategy expert helping a team with their Product Vision Board.

    Project: {project_name}
    Section: {section_display}
    {f'Context: {context}' if context else ''}

    Based on the project name and any context provided, please provide 3-5 concise, clear, and strategic suggestions for the {section_display} section of the Product Vision Board.

    Return ONLY the suggestions, one per line, with no numbering, headers, or other text.
    """
    
    result = await generate_ai_suggestions(prompt)
    
    # Parse the response - split by newlines and clean up
    suggestions = [line.strip() for line in result["content"].split("\n") if line.strip()]
    
    # Remove any bullet points or numbering
    suggestions = [s.lstrip("- ").lstrip("* ").lstrip("1234567890). ") for s in suggestions]
    
    return suggestions


async def generate_bmc_suggestions(
    project_name: str,
    section: str,
    context: Optional[str] = None
) -> List[str]:
    """
    Generate Business Model Canvas suggestions based on the project and section.
    
    Args:
        project_name: The name of the project
        section: The BMC section (key_partners, key_activities, etc.)
        context: Optional additional context about the project
        
    Returns:
        List of suggestions
    """
    # Map section names to user-friendly names
    section_names = {
        "key_partners": "Key Partners",
        "key_activities": "Key Activities",
        "key_resources": "Key Resources",
        "value_propositions": "Value Propositions",
        "customer_relationships": "Customer Relationships",
        "channels": "Channels",
        "customer_segments": "Customer Segments",
        "cost_structure": "Cost Structure",
        "revenue_streams": "Revenue Streams"
    }
    
    section_display = section_names.get(section, section.replace("_", " ").title())
    
    prompt = f"""
    You are a business model expert helping a team with their Business Model Canvas.

    Project: {project_name}
    Section: {section_display}
    {f'Context: {context}' if context else ''}

    Based on the project name and any context provided, please provide 3-5 concise, clear, and insightful suggestions for the {section_display} section of the Business Model Canvas.

    Return ONLY the suggestions, one per line, with no numbering, headers, or other text.
    """
    
    result = await generate_ai_suggestions(prompt)
    
    # Parse the response - split by newlines and clean up
    suggestions = [line.strip() for line in result["content"].split("\n") if line.strip()]
    
    # Remove any bullet points or numbering
    suggestions = [s.lstrip("- ").lstrip("* ").lstrip("1234567890). ") for s in suggestions]
    
    return suggestions


async def generate_persona_suggestions(
    project_name: str,
    category: str,
    context: Optional[str] = None,
    persona_name: Optional[str] = None
) -> List[str]:
    """
    Generate User Persona suggestions based on the project and category.
    
    Args:
        project_name: The name of the project
        category: 'Goal', 'Need', 'Pain Point', or 'Motivation'
        context: Optional additional context about the project
        persona_name: Optional name of the persona
        
    Returns:
        List of suggestions
    """
    # Map category names to user-friendly descriptions
    category_descriptions = {
        "Goal": "things the persona wants to achieve or accomplish",
        "Need": "essential requirements or necessities the persona has",
        "Pain Point": "challenges, frustrations, or problems the persona experiences",
        "Motivation": "factors that drive the persona's behavior or decisions"
    }
    
    category_description = category_descriptions.get(category, f"{category}s")
    
    prompt = f"""
    You are a UX researcher and user persona expert helping a team define detailed user personas.

    Project: {project_name}
    Persona: {persona_name or "User persona"}
    Category: {category} ({category_description})
    {f'Context: {context}' if context else ''}

    Based on the project name and any context provided, please suggest 4-6 concise, specific, and realistic {category.lower()}s for this user persona.

    These should be specific to the type of user that would interact with a product like {project_name}.

    Examples of good {category.lower()}s:
    - {category == "Goal" and "Complete tasks efficiently with minimal learning curve" or ""}
    - {category == "Need" and "Easy access to information without technical knowledge" or ""}
    - {category == "Pain Point" and "Frustrated by complex interfaces with too many options" or ""}
    - {category == "Motivation" and "To be seen as competent and efficient by colleagues" or ""}

    Return ONLY the suggestions, one per line, with no numbering, headers, or other text.
    """
    
    result = await generate_ai_suggestions(prompt)
    
    # Parse the response - split by newlines and clean up
    suggestions = [line.strip() for line in result["content"].split("\n") if line.strip()]
    
    # Remove any bullet points or numbering
    suggestions = [s.lstrip("- ").lstrip("* ").lstrip("1234567890). ") for s in suggestions]
    
    # Filter out empty lines and any that might be headers
    suggestions = [s for s in suggestions if s and not s.endswith(':')]
    
    return suggestions


async def generate_okr_objective_suggestions(
    project_name: str,
    context: Optional[str] = None
) -> List[str]:
    """
    Generate OKR objective suggestions based on the project.
    
    Args:
        project_name: The name of the project
        context: Optional additional context about the project
        
    Returns:
        List of suggestions
    """
    prompt = f"""
    You are an OKR expert helping a team define clear Objectives for their project.

    Project: {project_name}
    {f'Context: {context}' if context else ''}

    Based on the project name and any context provided, please provide 3-5 concise, clear, and inspiring Objective statements that follow OKR best practices.

    Good Objectives should be:
    - Qualitative, inspirational, and action-oriented
    - Time-bound (typically quarterly or annually)
    - Challenging yet achievable

    Return ONLY the objective statements, one per line, with no numbering, headers, or other text.
    """
    
    result = await generate_ai_suggestions(prompt)
    
    # Parse the response - split by newlines and clean up
    suggestions = [line.strip() for line in result["content"].split("\n") if line.strip()]
    
    # Remove any bullet points or numbering
    suggestions = [s.lstrip("- ").lstrip("* ").lstrip("1234567890). ") for s in suggestions]
    
    return suggestions


async def generate_okr_key_result_suggestions(
    objective: str,
    project_name: str,
    context: Optional[str] = None
) -> List[str]:
    """
    Generate OKR key result suggestions based on the objective.
    
    Args:
        objective: The objective statement
        project_name: The name of the project
        context: Optional additional context about the project
        
    Returns:
        List of suggestions
    """
    prompt = f"""
    You are an OKR expert helping a team define measurable Key Results for their Objective.

    Project: {project_name}
    Objective: {objective}
    {f'Context: {context}' if context else ''}

    Based on the objective and any context provided, please provide 3-5 concise, clear, and measurable Key Result statements that follow OKR best practices.

    Good Key Results should be:
    - Quantitative and measurable
    - Clear on what is being measured and how
    - Achievable yet challenging
    - Time-bound (typically quarterly or annually)

    Return ONLY the key result statements, one per line, with no numbering, headers, or other text.
    """
    
    result = await generate_ai_suggestions(prompt)
    
    # Parse the response - split by newlines and clean up
    suggestions = [line.strip() for line in result["content"].split("\n") if line.strip()]
    
    # Remove any bullet points or numbering
    suggestions = [s.lstrip("- ").lstrip("* ").lstrip("1234567890). ") for s in suggestions]
    
    return suggestions


async def generate_roadmap_suggestions(
    project_name: str,
    category: str,
    context: Optional[str] = None,
    current_items: Optional[List[str]] = None
) -> List[str]:
    """
    Generate roadmap item suggestions based on the project and category.
    
    Args:
        project_name: The name of the project
        category: The roadmap category (e.g., "now", "next", "later" or "high", "medium", "low")
        context: Optional additional context about the project
        current_items: Existing roadmap items
        
    Returns:
        List of suggestions
    """
    existing_items = ""
    if current_items and len(current_items) > 0:
        existing_items = "Existing roadmap items:\n" + "\n".join([f"- {item}" for item in current_items])
    
    # Determine if category is timeframe or priority based
    category_type = "timeframe"
    if category.lower() in ["high", "medium", "low"]:
        category_type = "priority"
    
    prompt = f"""
    You are a product roadmap expert helping a team plan their product roadmap.

    Project: {project_name}
    Category: {category} ({category_type})
    {f'Context: {context}' if context else ''}
    {existing_items}

    Based on the project name and any context provided, please suggest 3-5 concise, clear, and realistic roadmap items for the {category} {category_type} category.

    If timeframe category:
    - 'now' = immediate focus (current sprint/month)
    - 'next' = medium-term focus (1-3 months)
    - 'later' = future consideration (3+ months)

    If priority category:
    - 'high' = critical items that must be done first
    - 'medium' = important but not critical items
    - 'low' = nice-to-have items

    Make each suggestion specific, actionable, and appropriate for the timeframe/priority level.
    Return ONLY the suggestions, one per line, with no numbering, headers, or other text.
    """
    
    result = await generate_ai_suggestions(prompt)
    
    # Parse the response - split by newlines and clean up
    suggestions = [line.strip() for line in result["content"].split("\n") if line.strip()]
    
    # Remove any bullet points or numbering
    suggestions = [s.lstrip("- ").lstrip("* ").lstrip("1234567890). ") for s in suggestions]
    
    return suggestions


async def generate_rice_suggestions(
    project_name: str,
    context: Optional[str] = None,
    current_items: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Generate RICE matrix item suggestions based on the project.
    
    Args:
        project_name: The name of the project
        context: Optional additional context about the project
        current_items: Existing RICE items names
        
    Returns:
        List of RICE item dictionaries with suggested name, description and scores
    """
    existing_items = ""
    if current_items and len(current_items) > 0:
        existing_items = "Existing features in this project:\n" + "\n".join([f"- {item}" for item in current_items])
    
    prompt = f"""
    You are a product prioritization expert helping a team with their RICE prioritization matrix.

    Project: {project_name}
    {f'Context: {context}' if context else ''}
    {existing_items}

    Based on the project name and any context provided, please suggest 4-5 potential features or initiatives that could be considered for this project.
    For each feature, provide:
    1. A clear, concise name (max 8 words)
    2. A brief description of the feature (1-2 sentences)
    3. Suggested RICE scores (all scores should be on a scale of 0-10, except Effort which is 1-10):
       - Reach score (0-10): How many users/customers will this feature impact?
       - Impact score (0-10): How much will it impact each user?
       - Confidence score (0-10): How confident are you in your estimates?
       - Effort score (1-10): How much work is required? (higher = more effort)
    
    Format your response as valid JSON with the following structure:
    [
      {{
        "name": "Feature name",
        "description": "Feature description",
        "reach_score": 8,
        "impact_score": 7,
        "confidence_score": 6,
        "effort_score": 5
      }},
      // Additional features...
    ]
    """
    
    result = await generate_ai_suggestions(prompt, max_tokens=1500, temperature=0.8)
    
    try:
        # Extract JSON from the content
        content = result["content"]
        # Handle potential markdown code blocks around the JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        suggestions = json.loads(content)
        return suggestions
    except json.JSONDecodeError as e:
        # If JSON parsing fails, try to extract as much information as possible
        print(f"JSON parsing error: {e} - Content: {result['content']}")
        return [
            {
                "name": "Feature suggestion (JSON parsing failed)",
                "description": "The AI generated text that couldn't be parsed. Please try again.",
                "reach_score": 5,
                "impact_score": 5,
                "confidence_score": 5,
                "effort_score": 5
            }
        ]
    except Exception as e:
        print(f"Error processing AI suggestions: {e}")
        return [] 