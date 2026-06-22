-- Migracao v2 -> v3 (hierarquia de acesso + novas areas de atuacao).
-- Rode UMA vez no SQL Editor do Supabase. E idempotente (pode rodar de novo sem efeito).
-- Obs.: se SUPABASE_DB_URL estiver configurado nos secrets, o app aplica as
-- alteracoes de ESTRUTURA sozinho no primeiro boot; este script tambem remapeia
-- os DADOS antigos das categorias.

-- 1) Colunas novas -------------------------------------------------------------
alter table public.usuarios
    add column if not exists nivel_hierarquia text not null default 'operacao';
alter table public.usuarios
    add column if not exists relatorios_permitidos jsonb not null default '[]'::jsonb;
alter table public.relatorios
    add column if not exists nivel_hierarquia text not null default 'operacao';

create index if not exists idx_relatorios_nivel on public.relatorios(nivel_hierarquia);

-- 2) Remapeia categorias antigas dos relatorios para as novas (MAIUSCULAS) ------
update public.relatorios set categoria = 'GERAL'       where categoria in ('Geral', 'geral');
update public.relatorios set categoria = 'VENDAS'      where categoria in ('Vendas', 'vendas');
update public.relatorios set categoria = 'MARKETING'   where categoria in ('Marketing', 'marketing');
update public.relatorios set categoria = 'FINANCEIRO'  where categoria in ('Financeiro', 'financeiro');
update public.relatorios set categoria = 'LOGISTICA'   where categoria in ('Logistica', 'Logística', 'logistica');
update public.relatorios set categoria = 'SUPRIMENTOS' where categoria in ('Suprimentos', 'suprimentos');
update public.relatorios set categoria = 'OPERACIONAL' where categoria in ('Operacoes', 'Operações', 'Operacional', 'operacional');
update public.relatorios set categoria = 'RH'          where categoria in ('rh', 'Rh');

-- 3) Remapeia as areas dos usuarios (jsonb array de texto) ----------------------
-- Substitui cada elemento legado pelo novo valor, preservando os demais.
update public.usuarios u
set categorias_permitidas = (
    select coalesce(jsonb_agg(distinct novo), '[]'::jsonb)
    from (
        select case elem
            when 'Geral'       then 'GERAL'
            when 'Vendas'      then 'VENDAS'
            when 'Marketing'   then 'MARKETING'
            when 'Financeiro'  then 'FINANCEIRO'
            when 'Logistica'   then 'LOGISTICA'
            when 'Logística'   then 'LOGISTICA'
            when 'Suprimentos' then 'SUPRIMENTOS'
            when 'Operacoes'   then 'OPERACIONAL'
            when 'Operações'   then 'OPERACIONAL'
            when 'Operacional' then 'OPERACIONAL'
            when 'RH'          then 'RH'
            else elem
        end as novo
        from jsonb_array_elements_text(u.categorias_permitidas) as elem
    ) s
    where novo in (
        'GERAL','FINANCEIRO','SUPRIMENTOS','INSUMOS','MARKETING','OPERACIONAL',
        'SOLINFITEC','LOGISTICA','VENDAS','DIRETORIA','RH','CONTROLADORIA'
    )
)
where jsonb_typeof(categorias_permitidas) = 'array';

-- 4) Admin enxerga tudo (nivel gestao) -----------------------------------------
update public.usuarios set nivel_hierarquia = 'gestao' where is_admin = true;
