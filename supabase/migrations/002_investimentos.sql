-- Investimentos da Soul (XP Soul + holding Route)
-- Fonte: extratos XP, atualizacao manual mensal via /soul aportes.
-- O dashboard le os CSVs de ingest/data_seed/; estas tabelas sao o espelho/arquivo.

create schema if not exists soul;

-- Razao de movimentacoes (aportes, resgates, migracoes, perdas, rentabilidade)
create table if not exists soul.investimentos_movimentos (
    id          bigserial primary key,
    data        date,
    mes         text,                 -- MM/YYYY (vazio = a alocar)
    conta       text not null,        -- XP Soul | Route
    tipo        text not null,        -- Aporte | Resgate | Migracao | Perda movimentacao | Rentabilidade | Saldo inicial
    valor       numeric(14,2) not null,  -- + entrada / - saida
    ativo       text,
    obs         text,
    updated_at  timestamptz default now()
);

create index if not exists ix_inv_mov_mes on soul.investimentos_movimentos (mes);
create index if not exists ix_inv_mov_conta on soul.investimentos_movimentos (conta);

-- Foto atual da carteira (snapshot de posicoes)
create table if not exists soul.investimentos_carteira (
    id              bigserial primary key,
    data_referencia date,
    conta           text,             -- XP Soul | Route
    titular         text,             -- Soul | Pai
    classe          text,             -- CDB | Fundo | Acao
    ativo           text,
    valor_aplicado  numeric(14,2),
    vencimento      text,
    posicao_atual   numeric(14,2),
    liquido         numeric(14,2),
    updated_at      timestamptz default now()
);

create index if not exists ix_inv_cart_titular on soul.investimentos_carteira (titular);
