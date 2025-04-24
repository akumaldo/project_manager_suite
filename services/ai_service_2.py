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
    # Debug output for API key
    api_key = settings.openrouter_api_key
    print(f"API Key: {api_key[:4]}...{api_key[-4:] if api_key and len(api_key) > 8 else 'NOT FOUND'}")
    
    # Ensure the API key has no extra whitespace
    api_key = api_key.strip() if api_key else ""
    
    # OpenRouter requires proper Bearer token format
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://product-discovery-hub.com" 
    }
    
    # Print headers (without full API key for security)
    headers_debug = headers.copy()
    if "Authorization" in headers_debug and headers_debug["Authorization"]:
        auth_value = headers_debug["Authorization"]
        if auth_value.startswith("Bearer "):
            token = auth_value.split("Bearer ")[1]
            if len(token) > 8:
                headers_debug["Authorization"] = f"Bearer {token[:4]}...{token[-4:]}"
    print(f"Request headers: {headers_debug}")
    
    payload = {
        "model": settings.openrouter_model,
        "messages": [{"role": "user", "content": prompt_text}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    # Make the API request
    try:
        async with httpx.AsyncClient() as client:
            print(f"Sending request to OpenRouter API")
            
            response = await client.post(
                f"{settings.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            
            print(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    if isinstance(error_json, dict):
                        error_detail = error_json.get('error', {}).get('message', error_detail)
                except:
                    pass
                
                print(f"Error response: {error_detail}")
                raise Exception(f"OpenRouter API error: {response.status_code} - {error_detail}")
            
            result = response.json()
            
            try:
                content = result["choices"][0]["message"]["content"]
                print(f"Successfully generated content")
                return {"content": content}
            except (KeyError, IndexError) as e:
                print(f"Unexpected API response format: {result}")
                raise Exception(f"Unexpected response format: {str(e)}")
    
    except httpx.RequestError as e:
        print(f"HTTPX Request error: {str(e)}")
        
        # Try fallback with synchronous requests
        print("Attempting fallback with synchronous requests...")
        
        # Import requests here to avoid dependency issues if not installed
        try:
            import requests
            import json
            import asyncio
            
            # Use a synchronous requests call in a thread to avoid blocking
            def make_sync_request():
                url = f"{settings.openrouter_base_url}/chat/completions"
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://product-discovery-hub.com"
                }
                
                print(f"Fallback headers: {headers['Authorization'][:10]}... (Content-Type: {headers['Content-Type']})")
                
                payload = {
                    "model": settings.openrouter_model,
                    "messages": [{"role": "user", "content": prompt_text}],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                
                if response.status_code != 200:
                    print(f"Fallback API error status: {response.status_code}")
                    print(f"Fallback API error text: {response.text}")
                    raise Exception(f"API error: {response.status_code} - {response.text}")
                
                return response.json()
            
            # Run the synchronous request in a thread pool
            loop = asyncio.get_event_loop()
            response_json = await loop.run_in_executor(None, make_sync_request)
            
            # Extract content from response
            content = response_json["choices"][0]["message"]["content"]
            print("Fallback method successful!")
            
            return {
                "content": content
            }
        except ImportError:
            print("Requests module not available for fallback")
            raise e
        except Exception as fallback_error:
            print(f"Fallback method also failed: {str(fallback_error)}")
            raise e
    except Exception as e:
        print(f"General exception: {str(e)}")
        raise e


async def generate_framework_help(
    framework_name: str,
    max_tokens: int = 1500,
    temperature: float = 0.5
) -> Dict[str, str]:
    """
    Generate help content for a specific product management framework.
    
    Args:
        framework_name: Name of the framework (e.g., 'CSD Matrix', 'BMC', 'Personas')
        max_tokens: Maximum number of tokens to generate
        temperature: Controls randomness (lower = more focused)
        
    Returns:
        Dictionary containing the formatted help content
    """
    try:
        print(f"Generating help content for framework: {framework_name}")
        print(f"Checking API key availability: {bool(settings.openrouter_api_key)}")
        
        # Ensure OpenRouter API key is properly loaded
        if not settings.openrouter_api_key:
            print("WARNING: OpenRouter API key is not available!")
            # Provide mock content if API key is not available
            return {
                "content": f"""
# {framework_name}

This is placeholder content because the OpenRouter API key is not available.

## Description
The {framework_name} is a framework used in product management.

## Key Components
- Component 1
- Component 2
- Component 3

## When to Use
This framework is useful when...

## Examples
1. Example 1
2. Example 2
                """,
                "framework": framework_name
            }
        
        prompt = f"""
        You are a product management expert explaining frameworks to product teams.
        
        Please provide a comprehensive but concise explanation of the {framework_name} framework, including:
        
        1. A clear description of what the {framework_name} is and its purpose in product management
        2. The key components of the {framework_name} framework
        3. When and why product teams should use this framework
        4. 2-3 practical examples of how to use the {framework_name} effectively
        
        Format your response using Markdown for headings, lists, and emphasis where appropriate.
        Make the content informative yet accessible to product managers of varying experience levels.
        """
        
        # Try using the standard httpx method first
        try:
            result = await generate_ai_suggestions(prompt, max_tokens, temperature)
            print("Help content generated successfully")
            
            return {
                "content": result["content"],
                "framework": framework_name
            }
        except Exception as e:
            print(f"First attempt failed with: {str(e)}")
            
            # FALLBACK: Try a direct synchronous approach with requests
            print("Attempting fallback with synchronous requests...")
            
            # Import requests here to avoid dependency issues if not installed
            try:
                import requests
                import json
                import asyncio
                
                # Use a synchronous requests call in a thread to avoid blocking
                def make_sync_request():
                    api_key = settings.openrouter_api_key.strip()
                    url = f"{settings.openrouter_base_url}/chat/completions"
                    
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://product-discovery-hub.com"
                    }
                    
                    print(f"Fallback headers: {headers['Authorization'][:10]}... (Content-Type: {headers['Content-Type']})")
                    
                    payload = {
                        "model": settings.openrouter_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": max_tokens,
                        "temperature": temperature
                    }
                    
                    response = requests.post(url, headers=headers, json=payload, timeout=60)
                    
                    if response.status_code != 200:
                        print(f"Fallback API error status: {response.status_code}")
                        print(f"Fallback API error text: {response.text}")
                        raise Exception(f"API error: {response.status_code} - {response.text}")
                    
                    return response.json()
                
                # Run the synchronous request in a thread pool
                loop = asyncio.get_event_loop()
                response_json = await loop.run_in_executor(None, make_sync_request)
                
                # Extract content from response
                content = response_json["choices"][0]["message"]["content"]
                print("Fallback method successful!")
                
                return {
                    "content": content,
                    "framework": framework_name
                }
            except ImportError:
                print("Requests module not available for fallback")
                raise e
            except Exception as fallback_error:
                print(f"Fallback method also failed: {str(fallback_error)}")
                raise e
    
    except Exception as e:
        print(f"Error generating framework help: {str(e)}")
        
        # Last resort: Return mock content with the error message
        return {
            "content": f"""
# {framework_name}

Sorry, I couldn't generate content for this framework due to an API error.

Error details: {str(e)}

## Alternative
Please check back later or consult the product management documentation for information about {framework_name}.
            """,
            "framework": framework_name
        }


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