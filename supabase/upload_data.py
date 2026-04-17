"""Upload dos dados tratados para Supabase via Management API (INSERT em batches).

Lê CSVs de ingest/data_out/ e popula:
  - soul.dim_subgrupo_grupo
  - soul.dim_fornecedor_funcionario
  - soul.projetos
  - soul.contas_receber
  - soul.contas_pagar
"""
from pathlib import Path
import os
import sys
import json
import math
import pandas as pd
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

PROJECT_REF = os.getenv("SUPABASE_PROJECT_ID")
PAT = os.getenv("SUPABASE_PAT")
API = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
HEADERS = {"Authorization": f"Bearer {PAT}", "Content-Type": "application/json"}

DATA_OUT = ROOT / "ingest" / "data_out"
DATA_RAW = ROOT / "ingest" / "data_raw"


def run_sql(sql: str) -> list:
    r = requests.post(API, json={"query": sql}, headers=HEADERS, timeout=120)
    if not r.ok:
        print(f"ERRO HTTP {r.status_code}: {r.text[:500]}")
        r.raise_for_status()
    return r.json()


def esc(v):
    """Escapa valor para SQL."""
    if v is None or (isinstance(v, float) and math.isnan(v)) or pd.isna(v):
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    s = str(v).replace("'", "''")
    return f"'{s}'"


def insert_batches(table: str, cols: list[str], rows: list[list], batch_size: int = 200):
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        values = ",\n".join(
            "(" + ",".join(esc(v) for v in row) + ")" for row in batch
        )
        cols_sql = ",".join(cols)
        sql = f"INSERT INTO {table} ({cols_sql}) VALUES\n{values};"
        run_sql(sql)
        total += len(batch)
        print(f"    {total}/{len(rows)}...", end="\r", flush=True)
    print(f"    {total}/{len(rows)} OK            ")


def upload_dim_subgrupo():
    print("=> dim_subgrupo_grupo...")
    sys.path.insert(0, str(ROOT / "ingest"))
    from transform import load_de_para_subgrupo
    df = load_de_para_subgrupo()
    df = df.drop_duplicates(subset=["servico"])
    run_sql("TRUNCATE soul.dim_subgrupo_grupo;")
    rows = df[["servico", "subgrupo", "grupo"]].values.tolist()
    insert_batches("soul.dim_subgrupo_grupo", ["servico", "subgrupo", "grupo"], rows)


def upload_dim_fornecedor():
    print("=> dim_fornecedor_funcionario...")
    sys.path.insert(0, str(ROOT / "ingest"))
    from transform import load_de_para_fornecedor
    df = load_de_para_fornecedor().drop_duplicates(subset=["categoria"])
    run_sql("TRUNCATE soul.dim_fornecedor_funcionario;")
    rows = df[["categoria", "tipo"]].values.tolist()
    insert_batches("soul.dim_fornecedor_funcionario", ["categoria", "tipo_contato"], rows)


def _primeira_data_evento(row: pd.Series) -> tuple[pd.Timestamp | None, str | None]:
    """Retorna (data, tipo_evento) pegando a primeira coluna Data * nao nula."""
    for col in row.index:
        if col.startswith("Data ") and pd.notna(row[col]):
            tipo = col.replace("Data ", "")
            return pd.to_datetime(row[col], errors="coerce"), tipo
    return None, None


def _coletar_projeto_ids_extras() -> set[str]:
    """Projetos que aparecem em CR/CP mas NAO estao no ProjetoComValoresResumido."""
    cr = pd.read_excel(next(DATA_RAW.glob("Contas a Receber_*.xlsx")))
    cp = pd.read_csv(DATA_OUT / "contas_pagar_classificado.csv")
    ids = set()
    for df, col in [(cr, "Projeto"), (cp, "Projeto")]:
        for v in df[col].dropna().unique():
            s = str(v).strip()
            if s:
                ids.add(s)
    return ids


def upload_projetos(data_venda_map: dict[str, pd.Timestamp]):
    print("=> projetos...")
    df = pd.read_excel(next(DATA_RAW.glob("ProjetoComValoresResumido_*.xlsx")))
    df = df[df["Projeto"].notna()].copy()

    ids_principais = {str(p).strip() for p in df["Projeto"]}
    ids_extras = _coletar_projeto_ids_extras()
    ids_fantasmas = ids_extras - ids_principais

    resultados = []
    for _, r in df.iterrows():
        data_ev, tipo_ev = _primeira_data_evento(r)
        pid = str(r["Projeto"]).strip()
        resultados.append([
            pid,
            r.get("Instituição"),
            r.get("Cursos"),
            r.get("Semestre"),
            r.get("Resp. Atend."),
            r.get("Resp. Fin."),
            r.get("Meta de Adesão"),
            r.get("Ativos"),
            r.get("Sem Plano"),
            r.get("Desistentes"),
            r.get("Arrecad. Prevista (A)"),
            r.get("Pago (B)"),
            r.get("Em Atraso (C)"),
            r.get("QT Inadim."),
            r.get("A Vencer (D)"),
            r.get("A Receber (C+D)"),
            data_ev.strftime("%Y-%m-%d") if data_ev is not None and pd.notna(data_ev) else None,
            tipo_ev,
            data_venda_map.get(pid).strftime("%Y-%m-%d") if data_venda_map.get(pid) is not None else None,
        ])

    # fantasmas: projetos antigos que so aparecem em CR/CP (sem metadados)
    for pid in sorted(ids_fantasmas):
        dv = data_venda_map.get(pid)
        resultados.append([
            pid, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None,
            dv.strftime("%Y-%m-%d") if dv is not None else None,
        ])

    cols = [
        "projeto_id", "instituicao", "cursos", "semestre", "resp_atend", "resp_fin",
        "meta_adesao", "ativos", "sem_plano", "desistentes", "arrecad_prevista",
        "valor_pago", "em_atraso", "qt_inadim", "a_vencer", "a_receber_total",
        "data_evento", "tipo_evento", "data_venda",
    ]
    run_sql("TRUNCATE soul.projetos CASCADE;")
    insert_batches("soul.projetos", cols, resultados, batch_size=100)
    print(f"   ({len(ids_principais)} principais + {len(ids_fantasmas)} fantasmas)")


def calcular_data_venda_map() -> dict[str, pd.Timestamp]:
    df = pd.read_excel(next(DATA_RAW.glob("Contas a Receber_*.xlsx")))
    df["Data Vencimento"] = pd.to_datetime(df["Data Vencimento"], errors="coerce")
    return df.dropna(subset=["Projeto", "Data Vencimento"]).groupby("Projeto")["Data Vencimento"].min().to_dict()


def upload_contas_receber() -> None:
    print("=> contas_receber...")
    df = pd.read_excel(next(DATA_RAW.glob("Contas a Receber_*.xlsx")))
    for c in ("Data Vencimento", "Data Pagamento", "Data Crédito"):
        df[c] = pd.to_datetime(df[c], errors="coerce")

    rows = []
    for _, r in df.iterrows():
        rows.append([
            str(r["Projeto"]).strip() if pd.notna(r["Projeto"]) else None,
            str(r["Cód."]) if pd.notna(r["Cód."]) else None,
            r.get("Nome"),
            r.get("Pagador"),
            r.get("Valor"),
            r.get("Valor Pago"),
            r.get("Meio de Pag."),
            r["Data Vencimento"].strftime("%Y-%m-%d") if pd.notna(r["Data Vencimento"]) else None,
            r["Data Pagamento"].strftime("%Y-%m-%d") if pd.notna(r["Data Pagamento"]) else None,
            r["Data Crédito"].strftime("%Y-%m-%d") if pd.notna(r["Data Crédito"]) else None,
        ])
    cols = ["projeto_id", "codigo", "nome", "pagador", "valor", "valor_pago",
            "meio_pagamento", "data_vencimento", "data_pagamento", "data_credito"]
    run_sql("TRUNCATE soul.contas_receber;")
    insert_batches("soul.contas_receber", cols, rows, batch_size=200)


def upload_contas_pagar():
    print("=> contas_pagar...")
    df = pd.read_csv(DATA_OUT / "contas_pagar_classificado.csv")

    def parse_date(x):
        if pd.isna(x) or x == "":
            return None
        try:
            return pd.to_datetime(x).strftime("%Y-%m-%d")
        except Exception:
            return None

    rows = []
    for _, r in df.iterrows():
        rows.append([
            r.get("Empresa"), r.get("Descrição"),
            str(r["Projeto"]).strip() if pd.notna(r.get("Projeto")) else None,
            r.get("Evento"),
            parse_date(r.get("Data Emissão NF")),
            r.get("Tipo Vencimento"),
            parse_date(r.get("Vencimento")),
            parse_date(r.get("Vencimento Útil")),
            r.get("Valor Parcela"), r.get("Total Conta"),
            parse_date(r.get("Pagamento")),
            r.get("Valor Pagamento"), r.get("Valor Multa"), r.get("Valor Juros"),
            r.get("Valor Desconto"), r.get("Parcela"), r.get("Impostos"),
            r.get("Serviço"), r.get("Serviço_norm"),
            r.get("Categoria"), r.get("Fornecedor"), r.get("C. Custo"),
            r.get("Conta Origem"), r.get("Forma Pag."), r.get("NF"),
            parse_date(r.get("Compet.")),
            r.get("Valor da Venda"),
            r.get("Val. Venda - Val. Parcela (BV previsto)"),
            r.get("Val. Venda - Val. Pagamento (BV realizado)"),
            r.get("Observação Parcela"), r.get("Status Liberação"),
            r.get("Responsável"),
            r.get("subgrupo"), r.get("grupo"), r.get("tipo_contato"),
        ])
    cols = [
        "empresa", "descricao", "projeto_id", "evento",
        "data_emissao_nf", "tipo_vencimento", "vencimento", "vencimento_util",
        "valor_parcela", "total_conta", "pagamento",
        "valor_pagamento", "valor_multa", "valor_juros", "valor_desconto",
        "parcela", "impostos",
        "servico", "servico_norm", "categoria", "fornecedor", "centro_custo",
        "conta_origem", "forma_pagamento", "nf", "competencia",
        "valor_venda", "bv_previsto", "bv_realizado",
        "observacao_parcela", "status_liberacao", "responsavel",
        "subgrupo", "grupo", "tipo_contato",
    ]
    run_sql("TRUNCATE soul.contas_pagar;")
    insert_batches("soul.contas_pagar", cols, rows, batch_size=150)


def contagem_final():
    print("\n=> Contagem final:")
    res = run_sql("""
      select 'projetos' as tabela, count(*)::int as n from soul.projetos
      union all select 'contas_receber', count(*)::int from soul.contas_receber
      union all select 'contas_pagar', count(*)::int from soul.contas_pagar
      union all select 'dim_subgrupo_grupo', count(*)::int from soul.dim_subgrupo_grupo
      union all select 'dim_fornecedor_funcionario', count(*)::int from soul.dim_fornecedor_funcionario
      order by 1
    """)
    for row in res:
        print(f"   {row['tabela']:<30s} {row['n']:>6d}")


def main():
    upload_dim_subgrupo()
    upload_dim_fornecedor()
    data_venda_map = calcular_data_venda_map()
    upload_projetos(data_venda_map)
    upload_contas_receber()
    upload_contas_pagar()
    contagem_final()


if __name__ == "__main__":
    main()