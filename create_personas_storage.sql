-- Create a storage bucket for persona photos
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'personas',
  'personas',
  TRUE, -- Set to public so URLs can be accessed without authentication
  5242880, -- 5MB file size limit
  ARRAY['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml']::text[] -- Allow only image files
)
ON CONFLICT (id) DO NOTHING;

-- Note: Storage policies need to be configured through the Supabase dashboard:
-- 1. Navigate to Storage → Buckets → personas → Policies
-- 2. Add the following policies:
--    - SELECT policy: Allow public read access (definition: true)
--    - INSERT policy: Allow authenticated users to upload (definition: auth.role() = 'authenticated')
--    - UPDATE policy: Allow authenticated users to update (definition: auth.role() = 'authenticated') 