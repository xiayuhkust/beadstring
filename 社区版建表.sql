-- BeadString 社区版 P2a 建表脚本（2026-07-22 功能定稿后修订）
-- 用法：Supabase Dashboard → SQL Editor → New query → 全文粘贴 → Run
-- 四张表：profiles(用户资料) / strands(云端串档) / states(轻状态同步) / amens(造就了我，P2b 启用)
-- 已定功能：理由默认私有、串成时勾选公开(is_public)；重串覆盖只留最新(unique)；
--          读经位置+串珠历跟人走(states)；登录=邮箱魔法链接
-- 全部开启行级安全(RLS)：anon key 只能在登录后按策略读写自己的数据

-- ============ profiles ============
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  display_name text not null default '',
  level int not null default 0,
  created_at timestamptz not null default now()
);
alter table public.profiles enable row level security;
create policy "profiles_select_all" on public.profiles
  for select using (true);
create policy "profiles_insert_own" on public.profiles
  for insert with check (auth.uid() = id);
create policy "profiles_update_own" on public.profiles
  for update using (auth.uid() = id);

-- ============ strands（云端串档）============
create table public.strands (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  pair_key text not null,                  -- 章对键，如 "Exod34|Jonah4"（排序后连接）
  refs jsonb not null,                     -- [refA, refB] 展示用出处
  anchors jsonb not null default '[]',     -- A 侧划中的词
  anchors_b jsonb not null default '[]',   -- B 侧划中的词
  reason text not null default '',
  is_public boolean not null default false, -- 串成时勾选「愿意挂出来」才为 true
  lang text not null default 'en',
  meta jsonb not null default '{}',        -- {wall, votes, words, debate}
  strung_on date not null,
  updated_at timestamptz not null default now(),
  unique (user_id, pair_key)
);
alter table public.strands enable row level security;
-- P2a：串档一律只有本人可读（is_public 只是记下用户意愿）；
-- P2b 众人的注脚再加服务端"先写后看"放开策略（security definer 函数：
-- 读者必须已串同一 pair_key 才能读别人 is_public=true 的理由）
create policy "strands_select_own" on public.strands
  for select using (auth.uid() = user_id);
create policy "strands_insert_own" on public.strands
  for insert with check (auth.uid() = user_id);
create policy "strands_update_own" on public.strands
  for update using (auth.uid() = user_id);
create policy "strands_delete_own" on public.strands
  for delete using (auth.uid() = user_id);
create index strands_user_idx on public.strands (user_id);
create index strands_pair_idx on public.strands (pair_key) where is_public; -- P2b 注脚查询用

-- ============ states（轻状态同步：读经位置 reading:<lang> / 串珠历 days）============
create table public.states (
  user_id uuid not null references auth.users(id) on delete cascade,
  key text not null,
  value jsonb not null default '{}',
  updated_at timestamptz not null default now(),
  primary key (user_id, key)
);
alter table public.states enable row level security;
create policy "states_select_own" on public.states
  for select using (auth.uid() = user_id);
create policy "states_insert_own" on public.states
  for insert with check (auth.uid() = user_id);
create policy "states_update_own" on public.states
  for update using (auth.uid() = user_id);
create policy "states_delete_own" on public.states
  for delete using (auth.uid() = user_id);

-- ============ amens（造就了我，P2b 才在前端启用）============
create table public.amens (
  strand_id bigint not null references public.strands(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (strand_id, user_id)
);
alter table public.amens enable row level security;
create policy "amens_select_all" on public.amens
  for select using (true);
create policy "amens_insert_own" on public.amens
  for insert with check (auth.uid() = user_id);
create policy "amens_delete_own" on public.amens
  for delete using (auth.uid() = user_id);

-- ============ P2b 众人的注脚（2026-07-23 已由管理 API 执行；同日按用户决定改为任何人可看）============
-- 现行版：任何人（含匿名）可读公开注脚，按「造就了我」数排序；前端以折叠链接保留"先自己想"的摩擦
-- （下方为首版"先写后看"存档，现行版见文件末尾）
create or replace function public.bead_notes(p_pair_key text)
returns table (display_name text, reason text, lang text, strung_on date)
language sql security definer set search_path = public stable
as $$
  select p.display_name, s.reason, s.lang, s.strung_on
  from strands s join profiles p on p.id = s.user_id
  where s.pair_key = p_pair_key and s.is_public and s.reason <> ''
    and s.user_id <> auth.uid()
    and exists (select 1 from strands mine
                where mine.user_id = auth.uid() and mine.pair_key = p_pair_key)
  order by s.strung_on desc limit 50
$$;
revoke all on function public.bead_notes(text) from public;
grant execute on function public.bead_notes(text) to authenticated;

-- ============ P2b 现行版 bead_notes（任何人可看 + 造就计数，2026-07-23）============
drop function if exists public.bead_notes(text);
create or replace function public.bead_notes(p_pair_key text)
returns table (sid bigint, display_name text, reason text, lang text, strung_on date, amen_count int, mine boolean)
language sql security definer set search_path = public stable
as $$
  select s.id, p.display_name, s.reason, s.lang, s.strung_on,
         (select count(*) from amens a where a.strand_id = s.id)::int,
         (auth.uid() is not null and exists
            (select 1 from amens a2 where a2.strand_id = s.id and a2.user_id = auth.uid()))
  from strands s join profiles p on p.id = s.user_id
  where s.pair_key = p_pair_key and s.is_public and s.reason <> ''
    and (auth.uid() is null or s.user_id <> auth.uid())
  order by 6 desc, s.strung_on desc limit 50
$$;
revoke all on function public.bead_notes(text) from public;
grant execute on function public.bead_notes(text) to anon, authenticated;
