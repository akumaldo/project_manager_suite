-- Create the framework_links table to store links between different framework items
CREATE TABLE IF NOT EXISTS framework_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    source_item_id UUID NOT NULL,
    source_item_type TEXT NOT NULL,
    target_item_id UUID NOT NULL,
    target_item_type TEXT NOT NULL,
    link_type TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for faster queries
CREATE INDEX idx_framework_links_project_id ON framework_links(project_id);
CREATE INDEX idx_framework_links_user_id ON framework_links(user_id);
CREATE INDEX idx_framework_links_source ON framework_links(source_item_id, source_item_type);
CREATE INDEX idx_framework_links_target ON framework_links(target_item_id, target_item_type);

-- Add triggers for updated_at
CREATE TRIGGER update_framework_links_updated_at_trigger
BEFORE UPDATE ON framework_links
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE framework_links ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Users can view their own framework links" 
ON framework_links FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own framework links" 
ON framework_links FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own framework links" 
ON framework_links FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own framework links" 
ON framework_links FOR DELETE 
USING (auth.uid() = user_id); 