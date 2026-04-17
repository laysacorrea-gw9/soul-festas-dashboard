"""
transform.py — PIPELINE UNICO de ingestao e classificacao.

Carrega os exports do SGE (.xlsx), aplica TODAS as regras de negocio,
cruza com Agenda/Balanco/CustoProjeto e gera os CSVs finais que o
dashboard consome DIRETAMENTE (sem reclassificar em runtime).

Uso:
    python transform.py

Saida em data_out/:
    - contas_pagar_final.csv
    - contas_receber_final.csv
    - projetos_final.csv
    - meta.json
"""
from pathlib import Path
import json
import sys
from datetime import datetime
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).parent
RAW = ROOT / "data_raw"
OUT = ROOT / "data_out"
OUT.mkdir(exist_ok=True)

# =====================================================================
# REGRAS DE NEGOCIO
# =====================================================================

# Normalizacao singular -> plural
SUBGRUPO_NORM = {
    "DESPESA FIXA": "DESPESAS FIXAS",
}

# Remap dos subgrupos do de-para original para os 4 subgrupos padrao Nibo
SUBGRUPO_NIBO = {
    # FIXAS
    "DESPESAS FIXAS": "DESPESAS FIXAS",
    "PESSOAL": "DESPESAS FIXAS",
    # VARIAVEIS
    "DESPESAS ADMINISTRATIVAS": "DESPESAS VARIÁVEIS",
    "DESPESAS GERAIS": "DESPESAS VARIÁVEIS",
    "MANUTENÇÃO CONSERVAÇÃO": "DESPESAS VARIÁVEIS",
    "OBRIGAÇÕES / IMPOSTOS": "DESPESAS VARIÁVEIS",
    "OUTROS": "DESPESAS VARIÁVEIS",
    "DESPESAS FINANCEIRAS": "DESPESAS VARIÁVEIS",
    # EVENTOS / TERCEIROS
    "DESPESAS COM EVENTOS": "DESPESAS COM EVENTOS",
    "DESPESAS COM TERCEIROS": "DESPESAS TERCEIROS",
}

# Centros de Custo que sao da CASA (operacional, nao do evento)
CC_CASA = ["Administrativo", "DP", "Comercial"]
# Centros de Custo que sao de EVENTOS
CC_EVENTOS = ["Eventos", "DEGUSTAÇÃO"]

# Prefixos de Categoria que indicam despesa fixa (nao evento, mesmo sem projeto)
CATEGORIA_FIXA_PREFIXES = ("001", "100", "110")


# =====================================================================
# LEITURA DE DADOS
# =====================================================================

def load_de_para_subgrupo() -> pd.DataFrame:
    """SERVICO -> SUBGRUPO -> GRUPO (do Excel Nibo + de_para_suplementar.csv)."""
    df = pd.read_excel(RAW / "modelo_nibo_pagas.xlsx", sheet_name="SUBGRUPO_GRUPO", header=1)
    df.columns = ["servico", "subgrupo", "grupo"]
    df = df.dropna(subset=["servico"]).copy()
    df["servico"] = df["servico"].astype(str).str.strip().str.upper()
    df["subgrupo"] = df["subgrupo"].astype(str).str.strip()
    df["grupo"] = df["grupo"].astype(str).str.strip()

    sup_path = ROOT / "de_para_suplementar.csv"
    if sup_path.exists():
        sup = pd.read_csv(sup_path)
        sup["servico"] = sup["servico"].astype(str).str.strip().str.upper()
        df = pd.concat([df, sup[["servico", "subgrupo", "grupo"]]], ignore_index=True)
        df = df.drop_duplicates(subset=["servico"], keep="last")
    return df


def load_de_para_fornecedor() -> pd.DataFrame:
    df = pd.read_excel(RAW / "modelo_nibo_pagas.xlsx", sheet_name="FORNECEDOR_FUNCIONARIO", header=None)
    df = df.dropna(how="all").copy()
    df.columns = ["categoria", "tipo"] + [f"x{i}" for i in range(len(df.columns) - 2)]
    df = df[["categoria", "tipo"]].dropna()
    df["categoria"] = df["categoria"].astype(str).str.strip()
    df["tipo"] = df["tipo"].astype(str).str.strip()
    return df


def load_agenda() -> dict:
    """Mapa Projeto -> data_evento (menor data da Agenda)."""
    files = list(RAW.glob("AgendaResumida_*.xlsx"))
    if not files:
        return {}
    df = pd.read_excel(files[0])
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    return (df.dropna(subset=["Data", "Projeto"])
              .groupby("Projeto")["Data"].min().to_dict())


def load_balanco_projeto() -> pd.DataFrame:
    """Balanco por projeto: Entrada/Saida Prevista vs Realizada."""
    files = list(RAW.glob("BalancoPorProjetoResumido*.xlsx"))
    if not files:
        return pd.DataFrame()
    df = pd.read_excel(files[0])
    df["Projeto"] = df["Projeto"].astype(str).str.strip()
    return df[["Projeto", "Entrada Prevista", "Entrada Realizada",
               "Saída Prevista", "Saída Realizada", "Saldo Previsto", "Saldo Realizado"]]


def load_custo_projeto() -> dict:
    """Mapa Projeto -> Descricao (primeiro nao-nulo do CustoDoProjeto)."""
    files = list(RAW.glob("CustoDoProjeto*.xlsx"))
    if not files:
        return {}
    df = pd.read_excel(files[0])
    df["Projeto"] = df["Projeto"].astype(str).str.strip()
    return (df.dropna(subset=["Descrição"])
              .groupby("Projeto")["Descrição"].first().to_dict())


def load_contas_pagar() -> pd.DataFrame:
    files = list(RAW.glob("Contas_a_Pagar_*.xlsx"))
    assert files, "Contas_a_Pagar nao encontrado"
    df = pd.read_excel(files[0])
    df["Serviço_norm"] = df["Serviço"].astype(str).str.strip().str.upper()
    for c in ("Compet.", "Pagamento", "Vencimento"):
        df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def load_contas_receber() -> pd.DataFrame:
    files = list(RAW.glob("Contas a Receber_*.xlsx"))
    assert files, "Contas a Receber nao encontrado"
    df = pd.read_excel(files[0])
    for c in ("Data Vencimento", "Data Pagamento", "Data Crédito"):
        df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def load_contas_nao_recebidas() -> pd.DataFrame:
    """Parcelas em aberto (não pagas). Export SGE: Status = Não Pagas."""
    files = list(RAW.glob("Contas nao recebida*"))
    if not files:
        return pd.DataFrame()
    df = pd.read_excel(files[0])
    for c in ("Data Vencimento", "Data Pagamento", "Data Crédito"):
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def load_projetos() -> pd.DataFrame:
    files = list(RAW.glob("ProjetoComValoresResumido_*.xlsx"))
    assert files, "ProjetoComValoresResumido nao encontrado"
    return pd.read_excel(files[0])


# =====================================================================
# TRANSFORMACOES
# =====================================================================

def processar_contas_pagar(pagar: pd.DataFrame, dp_sub: pd.DataFrame,
                            dp_forn: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica TODAS as regras de classificacao em Contas a Pagar."""
    df = pagar.merge(
        dp_sub[["servico", "subgrupo", "grupo"]],
        left_on="Serviço_norm", right_on="servico", how="left",
    ).drop(columns=["servico"], errors="ignore")

    df = df.merge(
        dp_forn, left_on="Categoria", right_on="categoria", how="left",
    ).drop(columns=["categoria"], errors="ignore").rename(columns={"tipo": "tipo_contato"})

    # log nao classificados (antes de aplicar regras)
    nao_class = df[df["grupo"].isna() & df["Serviço"].notna()][
        ["Serviço", "Categoria", "Fornecedor", "Valor Parcela", "Compet."]
    ].copy()

    # === REGRA 1: Normalizacao de subgrupos ===
    df["subgrupo"] = df["subgrupo"].replace(SUBGRUPO_NORM)

    # === REGRA 2: Remap para 4 subgrupos Nibo ===
    df["subgrupo"] = df["subgrupo"].map(SUBGRUPO_NIBO).fillna(df["subgrupo"])

    # === REGRA 3: Se tem projeto -> DESPESAS COM EVENTOS ===
    tem_proj = df["Projeto"].notna() & (df["Projeto"].astype(str).str.strip() != "") & (df["Projeto"].astype(str) != "nan")
    df.loc[tem_proj, "subgrupo"] = "DESPESAS COM EVENTOS"

    # === REGRA 4: Sem projeto + CC casa + cat fixa -> FIXAS; demais CC casa -> VARIAVEIS ===
    mask_err = (~tem_proj) & (df["subgrupo"] == "DESPESAS COM EVENTOS")
    cat_str = df["Categoria"].astype(str).fillna("")
    is_fixa = cat_str.str.startswith(CATEGORIA_FIXA_PREFIXES)
    cc_adm = df["C. Custo"].isin(CC_CASA)
    df.loc[mask_err & cc_adm & is_fixa, "subgrupo"] = "DESPESAS FIXAS"
    df.loc[mask_err & cc_adm & ~is_fixa, "subgrupo"] = "DESPESAS VARIÁVEIS"

    # === REGRA 5: Grupos de nivel 1 (EVENTOS vs OPERACIONAIS) ===
    df["grupo"] = df["subgrupo"].apply(
        lambda s: "DESPESAS COM EVENTOS" if s == "DESPESAS COM EVENTOS" else "DESPESAS OPERACIONAIS"
    )

    # === Campos calculados para o dashboard ===
    df["data_ref"] = df["Pagamento"].fillna(df["Vencimento"]).fillna(df["Compet."])
    df["valor_ref"] = df["Valor Pagamento"].fillna(df["Valor Parcela"])

    return df, nao_class


def processar_projetos(projetos: pd.DataFrame, mapa_agenda: dict,
                       balanco: pd.DataFrame, mapa_descricao: dict) -> pd.DataFrame:
    """Cruza projetos com Agenda + BalancoPorProjeto + Descricao."""
    df = projetos.copy()
    df["Projeto_str"] = df["Projeto"].astype(str).str.strip()
    df["data_evento"] = df["Projeto_str"].map(mapa_agenda)
    df["data_evento"] = pd.to_datetime(df["data_evento"], errors="coerce")

    # fallback: primeira "Data *" nao nula
    date_cols = [c for c in df.columns if c.startswith("Data ")]
    for c in date_cols:
        d = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
        df["data_evento"] = df["data_evento"].fillna(d)

    # tipo_evento: qual coluna "Data *" estava populada (primeira)
    def _tipo_ev(row):
        for c in date_cols:
            if pd.notna(row.get(c)):
                return c.replace("Data ", "")
        return None
    df["tipo_evento"] = df.apply(_tipo_ev, axis=1)

    # Merge balanco
    if not balanco.empty:
        df = df.merge(balanco, left_on="Projeto_str", right_on="Projeto",
                      how="left", suffixes=("", "_bal"))
        if "Projeto_bal" in df.columns:
            df = df.drop(columns=["Projeto_bal"])

    # Descricao do projeto (do CustoDoProjeto)
    df["Descrição Projeto"] = df["Projeto_str"].map(mapa_descricao)

    return df


# =====================================================================
# MAIN
# =====================================================================

def main():
    inicio = datetime.now()
    print("=" * 70)
    print("🔧 TRANSFORM.PY — Pipeline unico de ingestao e classificacao")
    print("=" * 70)

    # 1. LOAD
    print("\n[1/4] Carregando arquivos...")
    dp_sub = load_de_para_subgrupo()
    dp_forn = load_de_para_fornecedor()
    pagar = load_contas_pagar()
    receber = load_contas_receber()
    projetos = load_projetos()
    mapa_agenda = load_agenda()
    balanco = load_balanco_projeto()
    mapa_desc = load_custo_projeto()

    nao_recebidas = load_contas_nao_recebidas()

    print(f"   • Contas a Pagar:           {len(pagar)} lanc")
    print(f"   • Contas a Receber:         {len(receber)} lanc")
    print(f"   • Contas NÃO Recebidas:     {len(nao_recebidas)} lanc")
    print(f"   • Projetos:                 {len(projetos)}")
    print(f"   • Agenda (proj c/ data):    {len(mapa_agenda)}")
    print(f"   • Balanco projeto:          {len(balanco)}")
    print(f"   • Descricoes:               {len(mapa_desc)}")
    print(f"   • De-para SUBGRUPO_GRUPO:   {len(dp_sub)} regras")
    print(f"   • De-para FORN/FUNC:        {len(dp_forn)} regras")

    # 2. PROCESSAR
    print("\n[2/4] Aplicando regras de negocio em Contas a Pagar...")
    pagar_final, nao_class = processar_contas_pagar(pagar, dp_sub, dp_forn)
    cobertura = (pagar_final["grupo"].notna().sum() / len(pagar_final)) * 100
    print(f"   • Cobertura classificacao:  {cobertura:.1f}%")
    print(f"   • Nao classificados:        {len(nao_class)} lanc")
    print(f"   • Distribuicao por subgrupo:")
    for sub, qtd in pagar_final["subgrupo"].value_counts().items():
        print(f"       {sub:<30s} {qtd:>5d}")

    print("\n[3/4] Cruzando Projetos com Agenda + Balanco + Descricao...")
    projetos_final = processar_projetos(projetos, mapa_agenda, balanco, mapa_desc)
    tem_data = projetos_final["data_evento"].notna().sum()
    tem_desc = projetos_final["Descrição Projeto"].notna().sum()
    print(f"   • Projetos com data_evento: {tem_data}/{len(projetos_final)}")
    print(f"   • Projetos com descricao:   {tem_desc}/{len(projetos_final)}")

    # 3. SALVAR
    print("\n[4/4] Salvando CSVs finais...")
    pagar_final.to_csv(OUT / "contas_pagar_final.csv", index=False, encoding="utf-8")
    receber.to_csv(OUT / "contas_receber_final.csv", index=False, encoding="utf-8")
    if not nao_recebidas.empty:
        nao_recebidas.to_csv(OUT / "contas_nao_recebidas_final.csv", index=False, encoding="utf-8")
    projetos_final.to_csv(OUT / "projetos_final.csv", index=False, encoding="utf-8")
    nao_class.to_csv(OUT / "log_nao_classificado.csv", index=False, encoding="utf-8")

    # Meta
    meta = {
        "gerado_em": inicio.isoformat(),
        "fontes": {
            "pagar_xlsx": str(next(RAW.glob("Contas_a_Pagar_*.xlsx")).name),
            "receber_xlsx": str(next(RAW.glob("Contas a Receber_*.xlsx")).name),
            "projetos_xlsx": str(next(RAW.glob("ProjetoComValoresResumido_*.xlsx")).name),
        },
        "contagens": {
            "contas_pagar": len(pagar_final),
            "contas_receber": len(receber),
            "projetos": len(projetos_final),
            "cobertura_classificacao_pct": round(cobertura, 2),
            "nao_classificados": len(nao_class),
        },
        "totais_2026": {},
    }
    pg_2026 = pagar_final[pagar_final["data_ref"].dt.year == 2026]
    rc_2026 = receber[receber["Data Pagamento"].dt.year == 2026]
    meta["totais_2026"] = {
        "despesas": float(pg_2026["valor_ref"].sum()),
        "faturamento": float(rc_2026["Valor Pago"].sum()),
        "despesa_casa": float(pg_2026[pg_2026["C. Custo"].isin(CC_CASA)]["valor_ref"].sum()),
        "despesa_eventos": float(pg_2026[pg_2026["C. Custo"].isin(CC_EVENTOS)]["valor_ref"].sum()),
    }
    with open(OUT / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("✅ PIPELINE CONCLUIDO")
    print("=" * 70)
    for p in sorted(OUT.glob("*.csv")) + [OUT / "meta.json"]:
        if p.exists():
            print(f"   {p.name:<40s} {p.stat().st_size // 1024:>6d} KB")

    print(f"\n📊 Totais 2026:")
    print(f"   Faturamento:       R$ {meta['totais_2026']['faturamento']:>13,.2f}")
    print(f"   Despesas:          R$ {meta['totais_2026']['despesas']:>13,.2f}")
    print(f"     Casa:            R$ {meta['totais_2026']['despesa_casa']:>13,.2f}")
    print(f"     Eventos:         R$ {meta['totais_2026']['despesa_eventos']:>13,.2f}")
    lucro = meta['totais_2026']['faturamento'] - meta['totais_2026']['despesas']
    print(f"   Lucro Real:        R$ {lucro:>13,.2f}")

    duracao = (datetime.now() - inicio).total_seconds()
    print(f"\n⏱️  Tempo total: {duracao:.1f}s")


if __name__ == "__main__":
    main()
