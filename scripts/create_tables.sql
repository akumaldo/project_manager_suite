-- Create tables for Product Discovery Hub
-- Execute this in your Supabase SQL Editor

-- Projects Table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- CSD Items Table
CREATE TABLE IF NOT EXISTS csd_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK (category IN ('Certainty', 'Supposition', 'Doubt')),
    text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Product Vision Board Table
CREATE TABLE IF NOT EXISTS product_vision_boards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    vision TEXT,
    target_customers TEXT,
    customer_needs TEXT,
    product_features TEXT,
    business_goals TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Business Model Canvas Table
CREATE TABLE IF NOT EXISTS business_model_canvases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE UNIQUE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    key_partners TEXT,
    key_activities TEXT,
    key_resources TEXT,
    value_propositions TEXT,
    customer_relationships TEXT,
    channels TEXT,
    customer_segments TEXT,
    cost_structure TEXT,
    revenue_streams TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RICE Items Table
CREATE TABLE IF NOT EXISTS rice_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    reach_score INTEGER NOT NULL CHECK (reach_score >= 0 AND reach_score <= 10),
    impact_score INTEGER NOT NULL CHECK (impact_score >= 0 AND impact_score <= 10),
    confidence_score INTEGER NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 10),
    effort_score INTEGER NOT NULL CHECK (effort_score >= 1 AND effort_score <= 10),
    rice_score FLOAT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Roadmap Items Table
CREATE TABLE IF NOT EXISTS roadmap_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    quarter TEXT NOT NULL CHECK (quarter IN ('Q1', 'Q2', 'Q3', 'Q4')),
    year INTEGER NOT NULL CHECK (year >= 2000 AND year <= 2100),
    status TEXT NOT NULL CHECK (status IN ('Planned', 'In Progress', 'Completed', 'Delayed')),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Objectives Table
CREATE TABLE IF NOT EXISTS objectives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL CHECK (status IN ('Not Started', 'In Progress', 'Completed', 'At Risk')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Key Results Table
CREATE TABLE IF NOT EXISTS key_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    objective_id UUID NOT NULL REFERENCES objectives(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    current_value FLOAT NOT NULL DEFAULT 0,
    target_value FLOAT NOT NULL CHECK (target_value > 0),
    status TEXT NOT NULL CHECK (status IN ('Not Started', 'In Progress', 'Completed', 'At Risk')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the triggers
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name IN (
            'projects', 
            'csd_items', 
            'product_vision_boards', 
            'business_model_canvases', 
            'rice_items', 
            'roadmap_items', 
            'objectives', 
            'key_results'
        )
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS update_updated_at_trigger ON %I;
            CREATE TRIGGER update_updated_at_trigger
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE PROCEDURE update_updated_at_column();
        ', t, t);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create RLS policies
-- Enable RLS on all tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE csd_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_vision_boards ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_model_canvases ENABLE ROW LEVEL SECURITY;
ALTER TABLE rice_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE roadmap_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE objectives ENABLE ROW LEVEL SECURITY;
ALTER TABLE key_results ENABLE ROW LEVEL SECURITY;

-- Create policies for projects table
CREATE POLICY "Users can view their own projects" 
ON projects FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own projects" 
ON projects FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own projects" 
ON projects FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own projects" 
ON projects FOR DELETE 
USING (auth.uid() = user_id);

-- Create policies for csd_items table
CREATE POLICY "Users can view their own CSD items" 
ON csd_items FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own CSD items" 
ON csd_items FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own CSD items" 
ON csd_items FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own CSD items" 
ON csd_items FOR DELETE 
USING (auth.uid() = user_id);

-- Create similar policies for other tables
-- (Following the same pattern for all remaining tables)

-- Example for product_vision_boards
CREATE POLICY "Users can view their own PVB" 
ON product_vision_boards FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own PVB" 
ON product_vision_boards FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own PVB" 
ON product_vision_boards FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own PVB" 
ON product_vision_boards FOR DELETE 
USING (auth.uid() = user_id);

-- Create policies for roadmap_items table
CREATE POLICY "Users can view their own roadmap items" 
ON roadmap_items FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own roadmap items" 
ON roadmap_items FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own roadmap items" 
ON roadmap_items FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own roadmap items" 
ON roadmap_items FOR DELETE 
USING (auth.uid() = user_id);

-- Create indices for performance
CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_csd_items_project_id ON csd_items(project_id);
CREATE INDEX IF NOT EXISTS idx_csd_items_user_id ON csd_items(user_id);
CREATE INDEX IF NOT EXISTS idx_pvb_project_id ON product_vision_boards(project_id);
CREATE INDEX IF NOT EXISTS idx_pvb_user_id ON product_vision_boards(user_id);
CREATE INDEX IF NOT EXISTS idx_bmc_project_id ON business_model_canvases(project_id);
CREATE INDEX IF NOT EXISTS idx_bmc_user_id ON business_model_canvases(user_id);
CREATE INDEX IF NOT EXISTS idx_rice_project_id ON rice_items(project_id);
CREATE INDEX IF NOT EXISTS idx_rice_user_id ON rice_items(user_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_project_id ON roadmap_items(project_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_user_id ON roadmap_items(user_id);
CREATE INDEX IF NOT EXISTS idx_objectives_project_id ON objectives(project_id);
CREATE INDEX IF NOT EXISTS idx_objectives_user_id ON objectives(user_id);
CREATE INDEX IF NOT EXISTS idx_key_results_objective_id ON key_results(objective_id); 