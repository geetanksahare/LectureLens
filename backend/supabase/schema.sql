-- profiles mirrors auth.users, since Supabase Auth owns the actual login
create table profiles (
  id uuid primary key references auth.users(id),
  username text unique,
  created_at timestamptz default now()
);

-- one row per uploaded lecture (was lecture_history)
create table lectures (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles(id) not null,
  filename text not null,
  video_storage_path text not null,
  full_transcript text,
  requested_outputs text[] not null,
  status text not null default 'queued', -- queued | extracting_audio | transcribing | processing | completed | failed
  error_message text,
  processed_at timestamptz default now()
);

-- one row per Whisper segment (was transcript_segments) — unchanged shape
create table transcript_segments (
  id uuid primary key default gen_random_uuid(),
  lecture_id uuid references lectures(id) not null,
  segment_index int not null,
  start_time numeric not null,
  end_time numeric not null,
  text text not null
);

-- one row per generated artifact (new — this is what makes "choose your outputs" queryable)
create table job_outputs (
  id uuid primary key default gen_random_uuid(),
  lecture_id uuid references lectures(id) not null,
  output_type text not null, -- 'srt' | 'vtt' | 'summary_technical' | 'summary_simple' | 'quiz'
  storage_path text,
  content text,              -- for text-based outputs small enough to store inline (e.g. per-chunk summaries)
  created_at timestamptz default now()
);

-- one row per quiz attempt (was quiz_results) — unchanged shape
create table quiz_results (
  id uuid primary key default gen_random_uuid(),
  lecture_id uuid references lectures(id) not null,
  score int not null,
  total_questions int not null,
  taken_at timestamptz default now()
);

alter table lectures enable row level security;
alter table transcript_segments enable row level security;
alter table job_outputs enable row level security;
alter table quiz_results enable row level security;

create policy "own lectures" on lectures for all using (user_id = auth.uid());
-- segments/outputs/results scoped through their parent lecture's user_id
create policy "own segments" on transcript_segments for all using (
  lecture_id in (select id from lectures where user_id = auth.uid())
);
create policy "own outputs" on job_outputs for all using (
  lecture_id in (select id from lectures where user_id = auth.uid())
);
create policy "own quiz results" on quiz_results for all using (
  lecture_id in (select id from lectures where user_id = auth.uid())
);