from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Supabase configuration
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    
    # OpenRouter configuration
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "deepseek/deepseek-chat-v3-0324:free"
    
    # API configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:3000", "http://localhost:8080"]
    
    # PDF report configuration
    pdf_report_template_path: str = "templates/report_template.html"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create settings instance
settings = Settings() 