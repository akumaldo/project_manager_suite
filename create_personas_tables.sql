-- Create the trigger function for automatically updating timestamps
CREATE OR REPLACE FUNCTION public.set_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create personas table
CREATE TABLE public.personas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (char_length(name) > 0 AND char_length(name) <= 100),
    photo_url TEXT,
    quote TEXT,
    demographics TEXT,
    bio TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create persona_details table for Goals, Needs, Pain Points, and Motivations
CREATE TABLE public.persona_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id UUID NOT NULL REFERENCES public.personas(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    category TEXT NOT NULL CHECK (category IN ('Goal', 'Need', 'Pain Point', 'Motivation')),
    content TEXT NOT NULL CHECK (char_length(content) > 0 AND char_length(content) <= 500),
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create triggers to automatically update updated_at timestamp
CREATE TRIGGER set_updated_at_timestamp_personas
BEFORE UPDATE ON public.personas
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at_column();

CREATE TRIGGER set_updated_at_timestamp_persona_details
BEFORE UPDATE ON public.persona_details
FOR EACH ROW
EXECUTE FUNCTION public.set_updated_at_column();

-- Add Row Level Security (RLS) policies
ALTER TABLE public.personas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.persona_details ENABLE ROW LEVEL SECURITY;

-- CREATE Policy for personas table
CREATE POLICY "Users can view their own personas"
    ON public.personas
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own personas"
    ON public.personas
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own personas"
    ON public.personas
    FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own personas"
    ON public.personas
    FOR DELETE
    USING (auth.uid() = user_id);

-- CREATE Policy for persona_details table
CREATE POLICY "Users can view their own persona details"
    ON public.persona_details
    FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own persona details"
    ON public.persona_details
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own persona details"
    ON public.persona_details
    FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own persona details"
    ON public.persona_details
    FOR DELETE
    USING (auth.uid() = user_id);

-- Grant permissions to the service role
GRANT ALL ON public.personas TO service_role;
GRANT ALL ON public.persona_details TO service_role; 