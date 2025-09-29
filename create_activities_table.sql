-- Create activities table for activity logging
-- This table stores user activities for the activity feed

CREATE TABLE IF NOT EXISTS public.activities (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    leader_id UUID NOT NULL,
    user_id UUID NOT NULL,
    activity_type TEXT NOT NULL,
    description TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT activities_pkey PRIMARY KEY (id),
    CONSTRAINT check_activity_type CHECK (activity_type IN ('member_added', 'member_updated', 'member_deleted', 'attendance_marked', 'attendance_updated', 'attendance_cleared', 'attendance_incomplete', 'tutorial_uploaded', 'profile_updated'))
) TABLESPACE pg_default;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_activities_leader_id ON public.activities USING btree (leader_id) TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS idx_activities_created_at ON public.activities USING btree (created_at) TABLESPACE pg_default;
CREATE INDEX IF NOT EXISTS idx_activities_type ON public.activities USING btree (activity_type) TABLESPACE pg_default;

-- Enable Row Level Security
ALTER TABLE public.activities ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for leader-specific access
CREATE POLICY "Leaders can manage their own activities" ON public.activities
    FOR ALL USING (leader_id::text = auth.uid()::text);

-- Create trigger for updated_at (if needed in future)
CREATE OR REPLACE FUNCTION update_activities_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
