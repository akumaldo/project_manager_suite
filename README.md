# Product Discovery Hub - Backend

This is the backend for the Product Discovery Hub application, built with FastAPI and Supabase.

## Features

- Authentication via Supabase Auth (JWT verification)
- Project management
- CSD Matrix
- Product Vision Board (PVB)
- Business Model Canvas (BMC)
- RICE Prioritization
- Product Roadmap
- OKRs (Objectives and Key Results)
- AI-powered suggestions using OpenRouter API
- PDF report generation

## Technology Stack

- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Data Validation:** Pydantic V2
- **Database:** Supabase PostgreSQL
- **Authentication:** Supabase Auth
- **API Client:** supabase-py
- **PDF Generation:** xhtml2pdf
- **External API Calls:** httpx
- **Configuration:** pydantic-settings

## Setup

1. Clone the repository
2. Create a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the root directory with the following variables:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
   SUPABASE_JWT_SECRET=your_supabase_jwt_secret
   OPENROUTER_API_KEY=your_openrouter_api_key
   ```
5. Run the development server
   ```
   uvicorn main:app --reload
   ```

## Supabase Setup Requirements

The following tables should be created in Supabase:

- `profiles` (linked to `auth.users`)
- `projects` (linked to `auth.users.id` via a `user_id` column)
- `csd_items` (linked to `projects.id` via `project_id`)
- `product_vision_boards` (linked to `projects.id`, likely one row per project)
- `business_model_canvases` (linked to `projects.id`, likely one row per project)
- `rice_items` (linked to `projects.id`)
- `roadmap_items` (linked to `projects.id`)
- `objectives` (linked to `projects.id`)
- `key_results` (linked to `objectives.id`)

Row Level Security (RLS) policies should be configured for all tables to ensure users can only access their own data.

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key (for admin operations) |
| `SUPABASE_JWT_SECRET` | JWT secret for validating Supabase tokens |
| `OPENROUTER_API_KEY` | API key for OpenRouter (for AI suggestions) |
| `OPENROUTER_BASE_URL` | (Optional) Base URL for OpenRouter API |
| `OPENROUTER_MODEL` | (Optional) Model name for OpenRouter API |

## Development

To run tests:

```
pytest
```

## License

MIT 