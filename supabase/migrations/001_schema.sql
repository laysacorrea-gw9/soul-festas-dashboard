-- Soul Festas Dashboard — schema inicial
-- Cria tabelas de dados + dimensoes + config.
-- RLS sera adicionado em migration posterior quando multi-usuario entrar.

create schema if not exists soul;

-- =========================================================================
-- DIMENSOES (de-paras)
-- =========================================================================

create table if not exists soul.dim_subgrupo_grupo (
  servico         text primary key,
  subgrupo        text not null,
  grupo           text not null,
  fonte           text default 'original', -- original | heuristica | ia | manual
  confianca       numeric(3,2),
  updated_at      timestamptz default now()
);

create table if not exists soul.dim_fornecedor_funcionario (
  categoria       text primary key,
  tipo_contato    text not null check (tipo_contato in ('Fornecedor','Funcionário'))
);

-- =========================================================================
-- FATOS (dados SGE)
-- =========================================================================

create table if not exists soul.projetos (
  projeto_id          text primary key,        -- ex: "0001/2026"
  instituicao         text,
  cursos              text,
  semestre            text,
  resp_atend          text,
  resp_fin            text,
  meta_adesao         integer,
  ativos              integer,
  sem_plano           integer,
  desistentes         integer,
  arrecad_prevista    numeric(14,2),
  valor_pago          numeric(14,2),
  em_atraso           numeric(14,2),
  qt_inadim           integer,
  a_vencer            numeric(14,2),
  a_receber_total     numeric(14,2),
  data_evento         date,                    -- primeira data nao-nula das 11 colunas Data *
  tipo_evento         text,                    -- qual das 11 colunas estava populada
  data_venda          date,                    -- inferida: min(Data Vencimento) em contas_receber
  updated_at          timestamptz default now()
);

create table if not exists soul.contas_receber (
  id              bigserial primary key,
  projeto_id      text references soul.projetos(projeto_id) on delete cascade,
  codigo          text,
  nome            text,
  pagador         text,
  valor           numeric(14,2),
  valor_pago      numeric(14,2),
  meio_pagamento  text,
  data_vencimento date,
  data_pagamento  date,
  data_credito    date,
  updated_at      timestamptz default now()
);

create index if not exists idx_cr_projeto on soul.contas_receber(projeto_id);
create index if not exists idx_cr_venc on soul.contas_receber(data_vencimento);
create index if not exists idx_cr_pag on soul.contas_receber(data_pagamento);

create table if not exists soul.contas_pagar (
  id                  bigserial primary key,
  empresa             text,
  descricao           text,
  projeto_id          text references soul.projetos(projeto_id) on delete set null,
  evento              text,
  data_emissao_nf     date,
  tipo_vencimento     text,
  vencimento          date,
  vencimento_util     date,
  valor_parcela       numeric(14,2),
  total_conta         numeric(14,2),
  pagamento           date,
  valor_pagamento     numeric(14,2),
  valor_multa         numeric(14,2),
  valor_juros         numeric(14,2),
  valor_desconto      numeric(14,2),
  parcela             text,
  impostos            numeric(14,2),
  servico             text,
  servico_norm        text, -- uppercase p/ join com dim_subgrupo_grupo
  categoria           text,
  fornecedor          text,
  centro_custo        text,
  conta_origem        text,
  forma_pagamento     text,
  nf                  text,
  competencia         date,
  valor_venda         numeric(14,2),
  bv_previsto         numeric(14,2),
  bv_realizado        numeric(14,2),
  observacao_parcela  text,
  status_liberacao    text,
  responsavel         text,
  subgrupo            text, -- resolvido via servico_norm
  grupo               text,
  tipo_contato        text, -- resolvido via categoria
  updated_at          timestamptz default now()
);

create index if not exists idx_cp_projeto on soul.contas_pagar(projeto_id);
create index if not exists idx_cp_comp on soul.contas_pagar(competencia);
create index if not exists idx_cp_pag on soul.contas_pagar(pagamento);
create index if not exists idx_cp_grupo on soul.contas_pagar(grupo, subgrupo);

-- =========================================================================
-- CONFIG E METADADOS
-- =========================================================================

create table if not exists soul.config (
  chave       text primary key,
  valor       jsonb not null,
  updated_at  timestamptz default now()
);

-- valores iniciais
insert into soul.config (chave, valor) values
  ('percentual_comissao_alessandro', '{"pct": 0.03, "descricao": "3% sobre Lucro Real"}'::jsonb),
  ('meta_caixa_minimo', '{"valor": 600000, "descricao": "R$ 600K como reserva"}'::jsonb),
  ('grupos_despesas_soul', '{"grupos": ["CUSTOS OPERACIONAIS"], "descricao": "Grupos que entram no calculo de Despesas Soul (vs Eventos)"}'::jsonb)
on conflict (chave) do nothing;

create table if not exists soul.saldos_bancarios (
  id              bigserial primary key,
  data_referencia date not null,
  rede            numeric(14,2) default 0,
  bradesco        numeric(14,2) default 0,
  itau            numeric(14,2) default 0,
  valore          numeric(14,2) default 0,
  sgp             numeric(14,2) default 0,
  total           numeric(14,2) generated always as (coalesce(rede,0)+coalesce(bradesco,0)+coalesce(itau,0)+coalesce(valore,0)+coalesce(sgp,0)) stored,
  updated_at      timestamptz default now(),
  unique (data_referencia)
);

create table if not exists soul.ingestao_logs (
  id              bigserial primary key,
  executado_em    timestamptz default now(),
  arquivo_fonte   text,
  linhas_lidas    integer,
  linhas_inseridas integer,
  linhas_atualizadas integer,
  servicos_novos_detectados text[],
  erro            text,
  duracao_segundos numeric(10,2)
);

-- =========================================================================
-- VIEWS para o dashboard
-- =========================================================================

-- DRE mensal por Grupo/Subgrupo (regime competencia)
create or replace view soul.v_dre_mensal as
select
  to_char(competencia, 'YYYY-MM')      as mes,
  grupo,
  subgrupo,
  sum(valor_parcela)                   as total_competencia,
  sum(valor_pagamento)                 as total_caixa,
  count(*)                             as qtd_lancamentos
from soul.contas_pagar
where competencia is not null and grupo is not null
group by 1,2,3;

-- KPIs de topo (do mes corrente)
create or replace view soul.v_kpis_mes_corrente as
with mes as (select to_char(current_date, 'YYYY-MM') as m),
faturamento as (
  select coalesce(sum(valor_pago), 0) as val
  from soul.contas_receber, mes
  where to_char(data_pagamento, 'YYYY-MM') = mes.m
),
despesas as (
  select coalesce(sum(valor_pagamento), 0) as val
  from soul.contas_pagar, mes
  where to_char(pagamento, 'YYYY-MM') = mes.m
)
select faturamento.val as faturamento, despesas.val as despesas,
       (faturamento.val - despesas.val) as lucro_real
from faturamento, despesas;