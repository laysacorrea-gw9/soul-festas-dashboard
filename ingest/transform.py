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


def load_planilha_inadimplentes() -> pd.DataFrame:
    """Planilha SGE de inadimplentes (base já limpa pela equipe Soul).

    Diferente de Contas Não Recebidas (que tem TODAS as parcelas em aberto,
    inclusive de clientes cancelados), essa planilha vem com a base limpa —
    apenas inadimplentes que precisam ser cobrados.

    Procura recursivo porque a Laysa salva em subpastas datadas (ex: 08.05.2026/).
    Pega o arquivo mais recente por mtime.
    """
    files = list(RAW.rglob("PlanilhaClientesInadimplentes*.xlsx"))
    if not files:
        return pd.DataFrame()
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    df = pd.read_excel(files[0])
    for c in ("Vencimento", "Data Emissão", "Data Compra"):
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
    return df


def faixa_atraso(dias: int) -> str:
    """Classifica dias de atraso em faixas pra dashboard."""
    if dias <= 15:
        return "01-15 dias"
    if dias <= 30:
        return "16-30 dias"
    if dias <= 60:
        return "31-60 dias"
    if dias <= 90:
        return "61-90 dias"
    if dias <= 180:
        return "91-180 dias"
    return "180+ dias"


def processar_inadimplentes(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa e classifica a planilha de inadimplentes do SGE."""
    if df.empty:
        return df
    df = df.copy()
    df["Dias Atraso"] = pd.to_numeric(df["Dias Atraso"], errors="coerce").fillna(0).astype(int)
    df["Valor Nominal"] = pd.to_numeric(df["Valor Nominal"], errors="coerce").fillna(0)
    df["Valor Atualizado"] = pd.to_numeric(df["Valor Atualizado"], errors="coerce").fillna(0)
    df["Multa"] = pd.to_numeric(df.get("Multa"), errors="coerce").fillna(0)
    df["Juros"] = pd.to_numeric(df.get("Juros"), errors="coerce").fillna(0)

    df["faixa_atraso"] = df["Dias Atraso"].apply(faixa_atraso)

    # Telefone consolidado (prefere Celular, depois Tel Pagador)
    df["telefone"] = (
        df.get("Celular Cliente").astype(str).where(df.get("Celular Cliente").notna(), "")
        .replace("nan", "")
    )
    df.loc[df["telefone"] == "", "telefone"] = (
        df.get("Tel Pagador").astype(str).where(df.get("Tel Pagador").notna(), "").replace("nan", "")
    )

    # Categoria de acao: critico (>R$3k OU Corporativo) = Letícia; resto = régua SGE
    df["categoria_cobranca"] = "Régua SGE (automática)"
    df.loc[df["Valor Atualizado"] >= 3000, "categoria_cobranca"] = "Crítico — Letícia"
    df.loc[df["Tipo Projeto"] == "Corporativo", "categoria_cobranca"] = "Crítico — Letícia"

    return df


def salvar_snapshot_inadimplentes(df: pd.DataFrame) -> None:
    """Salva snapshot diário em data_out/historico/ pra evolução temporal."""
    if df.empty:
        return
    hist_dir = OUT / "historico"
    hist_dir.mkdir(exist_ok=True)
    snap_path = hist_dir / f"inadimplentes_{datetime.now().strftime('%Y-%m-%d')}.csv"
    df.to_csv(snap_path, index=False, encoding="utf-8")


def load_projetos_from_balanco() -> pd.DataFrame:
    """Constroi a tabela de projetos a partir do BalançoPorProjeto + Agenda.

    O ProjetoComValoresResumido foi descontinuado da pipeline porque ficava
    desatualizado entre semanas (precisava re-export manual). Agora derivamos
    tudo do Balanço (atualizado a cada export do SGE) + Agenda (data + tipo)."""
    bal_files = list(RAW.glob("BalancoPorProjetoResumido*.xlsx"))
    assert bal_files, "BalancoPorProjetoResumido nao encontrado"
    bal = pd.read_excel(bal_files[0])
    bal["Projeto"] = bal["Projeto"].astype(str).str.strip()
    bal = bal[bal["Projeto"].notna() & (bal["Projeto"] != "nan") & (bal["Projeto"] != "")]
    return bal[["Projeto", "Instituição", "Curso"]].rename(columns={"Curso": "Cursos"})


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
                       balanco: pd.DataFrame, mapa_descricao: dict,
                       agenda_df: pd.DataFrame = None) -> pd.DataFrame:
    """Cruza projetos com Agenda + BalancoPorProjeto + Descricao.

    Fonte primária = BalancoPorProjeto (sempre atualizado).
    Agenda = data + tipo do evento.
    CustoDoProjeto = descrição."""
    df = projetos.copy()
    df["Projeto_str"] = df["Projeto"].astype(str).str.strip()
    df["data_evento"] = df["Projeto_str"].map(mapa_agenda)
    df["data_evento"] = pd.to_datetime(df["data_evento"], errors="coerce")

    # tipo_evento: vem da Agenda (coluna "Evento")
    if agenda_df is not None and "Evento" in agenda_df.columns:
        ag = agenda_df.dropna(subset=["Projeto", "Evento"]).copy()
        ag["Projeto"] = ag["Projeto"].astype(str).str.strip()
        mapa_tipo = ag.groupby("Projeto")["Evento"].first().to_dict()
        df["tipo_evento"] = df["Projeto_str"].map(mapa_tipo)
    else:
        df["tipo_evento"] = None

    # Merge com balanço pra trazer Entrada/Saída Prevista/Realizada
    if not balanco.empty:
        df = df.merge(
            balanco[["Projeto", "Entrada Prevista", "Entrada Realizada",
                     "Saída Prevista", "Saída Realizada", "Saldo Previsto", "Saldo Realizado"]],
            left_on="Projeto_str", right_on="Projeto", how="left", suffixes=("", "_bal"),
        )
        if "Projeto_bal" in df.columns:
            df = df.drop(columns=["Projeto_bal"])

    # Descricao do projeto (do CustoDoProjeto)
    df["Descrição Projeto"] = df["Projeto_str"].map(mapa_descricao)

    return df


def load_agenda_df() -> pd.DataFrame:
    """Carrega a Agenda completa (não só o mapa) pra extrair tipo_evento."""
    files = list(RAW.glob("AgendaResumida_*.xlsx"))
    if not files:
        return pd.DataFrame()
    df = pd.read_excel(files[0])
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
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
    projetos = load_projetos_from_balanco()  # Fonte: BalancoPorProjeto (atualizado)
    mapa_agenda = load_agenda()
    agenda_df = load_agenda_df()
    balanco = load_balanco_projeto()
    mapa_desc = load_custo_projeto()

    nao_recebidas = load_contas_nao_recebidas()
    inadimplentes_raw = load_planilha_inadimplentes()

    print(f"   • Contas a Pagar:           {len(pagar)} lanc")
    print(f"   • Contas a Receber:         {len(receber)} lanc")
    print(f"   • Contas NÃO Recebidas:     {len(nao_recebidas)} lanc")
    print(f"   • Inadimplentes (base limpa):{len(inadimplentes_raw)} parcelas")
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
    projetos_final = processar_projetos(projetos, mapa_agenda, balanco, mapa_desc, agenda_df)
    tem_data = projetos_final["data_evento"].notna().sum()
    tem_desc = projetos_final["Descrição Projeto"].notna().sum()
    print(f"   • Projetos com data_evento: {tem_data}/{len(projetos_final)}")
    print(f"   • Projetos com descricao:   {tem_desc}/{len(projetos_final)}")

    # Inadimplentes (base limpa SGE)
    inadimplentes = processar_inadimplentes(inadimplentes_raw)

    # 3. SALVAR
    print("\n[4/4] Salvando CSVs finais...")
    pagar_final.to_csv(OUT / "contas_pagar_final.csv", index=False, encoding="utf-8")
    receber.to_csv(OUT / "contas_receber_final.csv", index=False, encoding="utf-8")
    if not nao_recebidas.empty:
        nao_recebidas.to_csv(OUT / "contas_nao_recebidas_final.csv", index=False, encoding="utf-8")
    projetos_final.to_csv(OUT / "projetos_final.csv", index=False, encoding="utf-8")
    nao_class.to_csv(OUT / "log_nao_classificado.csv", index=False, encoding="utf-8")
    if not inadimplentes.empty:
        inadimplentes.to_csv(OUT / "inadimplentes_final.csv", index=False, encoding="utf-8")
        salvar_snapshot_inadimplentes(inadimplentes)

    # Meta
    meta = {
        "gerado_em": inicio.isoformat(),
        "fontes": {
            "pagar_xlsx": str(next(RAW.glob("Contas_a_Pagar_*.xlsx")).name),
            "receber_xlsx": str(next(RAW.glob("Contas a Receber_*.xlsx")).name),
            "projetos_xlsx": str(next(RAW.glob("BalancoPorProjetoResumido*.xlsx")).name),
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
    if not inadimplentes.empty:
        meta["inadimplencia"] = {
            "parcelas": int(len(inadimplentes)),
            "pagadores_unicos": int(inadimplentes["Pagador"].nunique()),
            "valor_nominal": float(inadimplentes["Valor Nominal"].sum()),
            "valor_atualizado": float(inadimplentes["Valor Atualizado"].sum()),
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
