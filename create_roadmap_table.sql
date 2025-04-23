-- First check if there's an existing roadmap_items table and drop it if needed
DROP TABLE IF EXISTS roadmap_items CASCADE;

-- Create the roadmap_items table
CREATE TABLE roadmap_items (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  quarter VARCHAR(2) NOT NULL,
  year INTEGER NOT NULL, 
  status VARCHAR(20) DEFAULT 'Planned',
  priority VARCHAR(20) DEFAULT 'medium',
  timeframe VARCHAR(20) DEFAULT 'next',
  position INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries by project
CREATE INDEX roadmap_items_project_id_idx ON roadmap_items(project_id);

-- Create index for faster queries by user
CREATE INDEX roadmap_items_user_id_idx ON roadmap_items(user_id);

-- Row Level Security (RLS) policies
ALTER TABLE roadmap_items ENABLE ROW LEVEL SECURITY;

-- Policy for Select
CREATE POLICY roadmap_items_select_policy ON roadmap_items
  FOR SELECT USING (auth.uid() = user_id);

-- Policy for Insert 
CREATE POLICY roadmap_items_insert_policy ON roadmap_items
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy for Update
CREATE POLICY roadmap_items_update_policy ON roadmap_items
  FOR UPDATE USING (auth.uid() = user_id);

-- Policy for Delete
CREATE POLICY roadmap_items_delete_policy ON roadmap_items
  FOR DELETE USING (auth.uid() = user_id); 