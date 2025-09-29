CREATE TABLE IF NOT EXISTS public.attendance (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    leader_id UUID NOT NULL,
    member_id UUID NOT NULL,
    meeting_date DATE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('present', 'absent')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    CONSTRAINT attendance_pkey PRIMARY KEY (id),
    CONSTRAINT fk_leader FOREIGN KEY (leader_id) REFERENCES public.users(id) ON DELETE CASCADE,
    CONSTRAINT fk_member FOREIGN KEY (member_id) REFERENCES public.cell_members(id) ON DELETE CASCADE,
    UNIQUE (leader_id, member_id, meeting_date) -- Ensure only one attendance record per member per meeting
) TABLESPACE pg_default;

ALTER TABLE public.attendance ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Leaders can manage their own attendance" ON public.attendance
    FOR ALL USING (leader_id::text = auth.uid()::text);

CREATE OR REPLACE FUNCTION update_attendance_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_attendance_updated_at_trigger
BEFORE UPDATE ON public.attendance
FOR EACH ROW EXECUTE FUNCTION update_attendance_updated_at();
