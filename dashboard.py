"""Dashboard Soul Festas — MVP (versao simples e robusta)."""
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Soul Festas - Dashboard", layout="wide", page_icon="🎉")

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  /* ===== TEMA OFICIAL LOVABLE (tailwind config: soul-360) ===== */
  /* Primary: hsl(45 93% 47%) = AMARELO DOURADO */
  /* Accent: hsl(142 71% 45%) = VERDE */
  /* Background: hsl(222 47% 11%) = dark slate/navy */
  /* Card: hsl(222 47% 14%) */

  .stApp {
    background: hsl(222, 47%, 11%) !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
  }
  /* Esconde header/toolbar nativo do Streamlit */
  header[data-testid="stHeader"] { display: none !important; }
  .stDeployButton { display: none !important; }
  #MainMenu { display: none !important; }
  footer { display: none !important; }

  /* ===== TEXTO GRANDE (legibilidade máxima) ===== */
  html, body, .stApp, .stApp *, [class*="css"], p, div, span, label, li, td, th {
    font-size: 18px !important; color: hsl(210, 40%, 98%) !important; line-height: 1.6 !important;
  }
  /* Header Soul — forca tamanho grande */
  .soul-header .soul-title { font-size: 72px !important; font-weight: 800 !important; color: hsl(45,93%,47%) !important; line-height: 1 !important; letter-spacing: -0.03em !important; }
  .soul-header .soul-sub { font-size: 18px !important; color: hsl(215,20%,65%) !important; line-height: 1.4 !important; }
  .soul-header .soul-emoji { font-size: 52px !important; line-height: 1 !important; }
  h1, h1 *, .stApp h1 {
    font-size: 52px !important; font-weight: 800 !important;
    color: hsl(45, 93%, 47%) !important; letter-spacing: -0.02em !important;
    margin-bottom: 12px !important; line-height: 1.1 !important;
  }
  h2, h2 *, .stApp h2 {
    font-size: 36px !important; font-weight: 700 !important;
    color: hsl(210, 40%, 98%) !important; line-height: 1.2 !important;
    letter-spacing: -0.02em !important;
  }
  h3, h3 *, .stApp h3 {
    font-size: 26px !important; font-weight: 700 !important;
    color: hsl(210, 40%, 98%) !important;
  }
  h4, h4 *, .stApp h4 { font-size: 22px !important; font-weight: 600 !important; }
  .stCaption, [data-testid="stCaptionContainer"],
  [data-testid="stCaptionContainer"] * {
    color: hsl(215, 20%, 65%) !important; font-size: 16px !important;
  }
  .stMarkdown, .stMarkdown * { font-size: 18px !important; }
  .stMarkdown strong, .stMarkdown b { font-weight: 700 !important; }

  /* ===== METRIC CARDS GRANDES ===== */
  [data-testid="stMetric"] {
    background: hsl(222, 47%, 14%); border: 1px solid hsl(217, 33%, 22%);
    border-radius: 16px; padding: 24px 28px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25); transition: all 0.2s ease;
  }
  [data-testid="stMetric"]:hover { border-color: hsl(45, 93%, 47%); }
  [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
    font-size: 36px !important; font-weight: 800 !important;
    color: hsl(210, 40%, 98%) !important; line-height: 1.2 !important;
  }
  [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {
    font-size: 16px !important; color: hsl(215, 20%, 65%) !important;
    font-weight: 500 !important; margin-bottom: 10px !important;
  }
  [data-testid="stMetricDelta"], [data-testid="stMetricDelta"] * {
    color: hsl(142, 71%, 45%) !important; font-size: 15px !important; font-weight: 600 !important;
  }

  /* ===== TABS GRANDES ===== */
  .stTabs [data-baseweb="tab"] { font-size: 16px !important; padding: 10px 20px !important; }

  /* ===== DATAFRAMES GRANDES ===== */
  .stDataFrame, .stDataFrame * { font-size: 16px !important; }
  [data-testid="stDataFrame"] * { font-size: 16px !important; }

  /* ===== BOTÕES GRANDES ===== */
  .stButton > button { font-size: 16px !important; padding: 10px 18px !important; }
  div[data-testid="stButton"] > button[kind="secondary"] {
    font-size: 17px !important; padding: 8px 14px !important;
  }

  /* ===== INPUTS/DROPDOWNS GRANDES ===== */
  .stSelectbox, .stTextInput, .stNumberInput, .stSlider { font-size: 16px !important; }
  .stSelectbox input, .stTextInput input, .stNumberInput input {
    font-size: 17px !important;
    background: hsl(222, 47%, 14%) !important;
    color: #f1f5f9 !important;
    border: 1px solid hsl(217, 33%, 22%) !important;
  }
  /* NumberInput (inclui botoes +/-) */
  [data-testid="stNumberInput"] input { background: hsl(222, 47%, 14%) !important; color: #f1f5f9 !important; }
  [data-testid="stNumberInput"] button {
    background: hsl(222, 47%, 17%) !important;
    color: #f1f5f9 !important;
    border: 1px solid hsl(217, 33%, 22%) !important;
  }
  [data-testid="stNumberInput"] button:hover {
    background: hsl(45, 93%, 47%) !important;
    color: hsl(222, 47%, 11%) !important;
  }
  [data-testid="stNumberInput"] > div > div { background: hsl(222, 47%, 14%) !important; }
  [data-baseweb="popover"] li { font-size: 16px !important; padding: 12px 16px !important; }

  /* ===== TABS ===== */
  .stTabs [data-baseweb="tab-list"] {
    background: hsl(222, 47%, 14%); border-radius: 10px; padding: 4px;
    border: 1px solid hsl(217, 33%, 22%); gap: 2px;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent !important; border-radius: 6px !important;
    color: hsl(215, 20%, 65%) !important; font-weight: 500 !important;
    padding: 6px 12px !important; font-size: 13px !important;
  }
  .stTabs [aria-selected="true"] {
    background: hsl(45, 93%, 47%) !important;
    color: hsl(222, 47%, 11%) !important; font-weight: 600 !important;
  }

  /* ===== EXPANDERS ===== */
  .streamlit-expanderHeader, [data-testid="stExpander"] summary {
    background: hsl(222, 47%, 14%) !important;
    border: 1px solid hsl(217, 33%, 22%) !important; border-radius: 12px !important;
    font-weight: 600 !important; color: hsl(210, 40%, 98%) !important;
  }
  [data-testid="stExpander"] { border: none !important; background: transparent !important; }

  /* ===== BOTOES ===== */
  .stButton > button {
    background: hsl(217, 33%, 17%) !important; border: 1px solid hsl(217, 33%, 22%) !important;
    color: hsl(210, 40%, 98%) !important; border-radius: 8px !important; font-weight: 500 !important;
    font-size: 13px !important; transition: all 0.2s ease;
  }
  .stButton > button:hover {
    background: hsl(45, 93%, 47%) !important; border-color: hsl(45, 93%, 47%) !important;
    color: hsl(222, 47%, 11%) !important;
  }
  div[data-testid="stButton"] > button[kind="secondary"] {
    background: transparent !important; border: none !important;
    text-align: left !important; padding: 4px 8px !important;
  }
  div[data-testid="stButton"] > button[kind="secondary"]:hover {
    background: hsl(217, 33%, 17%) !important; color: hsl(45, 93%, 47%) !important;
  }

  /* ===== INPUTS ===== */
  .stSelectbox > div > div, .stTextInput > div > div, .stNumberInput > div > div {
    background: hsl(217, 33%, 17%) !important;
    border: 1px solid hsl(217, 33%, 22%) !important;
    border-radius: 8px !important; color: hsl(210, 40%, 98%) !important;
  }
  .stSelectbox input, .stTextInput input, .stNumberInput input { color: hsl(210, 40%, 98%) !important; }

  /* Dropdown (popover) */
  [data-baseweb="popover"] {
    background: hsl(222, 47%, 12%) !important;
    border: 1px solid hsl(217, 33%, 22%) !important;
    border-radius: 10px !important;
  }
  [data-baseweb="popover"] * { color: hsl(210, 40%, 98%) !important; }
  [data-baseweb="popover"] ul { background: hsl(222, 47%, 12%) !important; }
  [data-baseweb="popover"] li {
    background: hsl(222, 47%, 12%) !important;
    padding: 8px 12px !important; font-size: 13px !important;
  }
  [data-baseweb="popover"] li:hover {
    background: hsl(217, 33%, 17%) !important; color: hsl(45, 93%, 47%) !important;
  }
  [data-baseweb="popover"] li[aria-selected="true"] {
    background: hsl(45, 93%, 47%) !important; color: hsl(222, 47%, 11%) !important;
  }

  .stSlider [data-baseweb="slider"] > div { background: hsl(45, 93%, 47%) !important; }

  /* ===== DATAFRAMES ===== */
  .stDataFrame, [data-testid="stDataFrame"] {
    background: hsl(222, 47%, 14%) !important;
    border-radius: 12px !important; border: 1px solid hsl(217, 33%, 22%) !important;
    overflow: hidden;
  }
  .stDataFrame * { font-size: 13px !important; color: hsl(210, 40%, 98%) !important; }

  /* ===== ALERT BOXES ===== */
  .stAlert, [data-testid="stAlert"] {
    background: hsl(222, 47%, 14%) !important;
    border-radius: 12px !important; border-left-width: 4px !important;
  }

  /* ===== DIVIDERS ===== */
  hr { border-color: hsl(217, 33%, 22%) !important; margin: 1.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)


def brl(v):
    if pd.isna(v) or v == 0:
        return "R$ 0"
    s = f"{abs(v):,.0f}"
    s = s.replace(",", ".")
    return f"-R$ {s}" if v < 0 else f"R$ {s}"

ROOT = Path(__file__).parent
OUT = ROOT / "ingest" / "data_out"


def fmt(v):
    if pd.isna(v):
        return "-"
    return f"R$ {v:,.0f}".replace(",", ".")


# Todas as regras de negocio moram em ingest/transform.py
# Dashboard so LE os CSVs finais — zero reclassificacao em runtime


@st.cache_data
def load_data():
    """Le os CSVs ja processados pelo transform.py."""
    pagar = pd.read_csv(OUT / "contas_pagar_final.csv")
    receber = pd.read_csv(OUT / "contas_receber_final.csv")
    projetos = pd.read_csv(OUT / "projetos_final.csv")

    # Contas nao recebidas (parcelas em aberto)
    nr_path = OUT / "contas_nao_recebidas_final.csv"
    nao_recebidas = pd.read_csv(nr_path) if nr_path.exists() else pd.DataFrame()

    # Parse de datas
    for c in ("Compet.", "Pagamento", "Vencimento", "data_ref"):
        if c in pagar.columns:
            pagar[c] = pd.to_datetime(pagar[c], errors="coerce")
    for c in ("Data Vencimento", "Data Pagamento", "Data Crédito"):
        if c in receber.columns:
            receber[c] = pd.to_datetime(receber[c], errors="coerce")
        if c in nao_recebidas.columns:
            nao_recebidas[c] = pd.to_datetime(nao_recebidas[c], errors="coerce")
    if "data_evento" in projetos.columns:
        projetos["data_evento"] = pd.to_datetime(projetos["data_evento"], errors="coerce")

    # Compatibilidade retro: codigo antigo usa "data_evento_agenda"
    if "data_evento" in projetos.columns and "data_evento_agenda" not in projetos.columns:
        projetos["data_evento_agenda"] = projetos["data_evento"]

    return pagar, receber, projetos, nao_recebidas


@st.cache_data
def load_meta():
    """Le meta.json com info da ultima atualizacao."""
    import json
    meta_path = OUT / "meta.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    return {}


pagar, receber, projetos, nao_recebidas = load_data()

# Header profissional
st.markdown("""
<div class='soul-header'>
    <span class='soul-emoji'>🎉</span>
    <span class='soul-title'>SOUL EVENTOS</span>
    <br>
    <span class='soul-sub'>31.416.509/0001-43 · Dashboard de Gestão Financeira</span>
</div>
""", unsafe_allow_html=True)

hdr_l, hdr_c, hdr_r = st.columns([0.1, 2, 1.2])
with hdr_l:
    pass
with hdr_c:
    sub_a, sub_b = st.columns(2)
    with sub_a:
        ano = st.selectbox("Ano", [2026, 2025, 2024], index=0)
    with sub_b:
        meses_opts = ["Todos", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
                      "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        mes_sel = st.selectbox("Mês", meses_opts, index=0)
with hdr_r:
    _meta = load_meta()
    _geradoem = _meta.get("gerado_em", "")
    if _geradoem:
        try:
            _data_upd = pd.to_datetime(_geradoem).strftime("%d/%m/%Y %H:%M")
        except Exception:
            _data_upd = _geradoem
    else:
        _data_upd = "—"
    st.markdown(
        "<div style='text-align:right; padding-top: 28px;'>"
        "<div style='color: hsl(215, 20%, 65%); font-size: 12px;'>Última atualização</div>"
        f"<div style='color: hsl(45, 93%, 47%); font-weight: 700; font-size: 16px;'>{_data_upd}</div>"
        "</div>",
        unsafe_allow_html=True,
    )
st.markdown("<hr/>", unsafe_allow_html=True)

pagar_ano = pagar[pagar["data_ref"].dt.year == ano].copy()
receber_ano = receber[receber["Data Pagamento"].dt.year == ano].copy()

if mes_sel != "Todos":
    m_num = meses_opts.index(mes_sel)  # 1..12
    pagar_ano = pagar_ano[pagar_ano["data_ref"].dt.month == m_num]
    receber_ano = receber_ano[receber_ano["Data Pagamento"].dt.month == m_num]

faturamento = receber_ano["Valor Pago"].sum()
despesas_total = pagar_ano["valor_ref"].dropna().sum()

# Despesa Casa vs Evento via GRUPO (mesmo criterio do DRE)
desp_eventos = pagar_ano[pagar_ano["grupo"] == "DESPESAS COM EVENTOS"]["valor_ref"].dropna().sum()
desp_soul = pagar_ano[pagar_ano["grupo"] == "DESPESAS OPERACIONAIS"]["valor_ref"].dropna().sum()

lucro_real = faturamento - despesas_total

# Vendas/Pipeline: respeita filtro de mes (via data_evento da Agenda)
if "data_evento_agenda" in projetos.columns:
    projetos["_data_ev"] = pd.to_datetime(projetos["data_evento_agenda"], errors="coerce")
else:
    projetos["_data_ev"] = pd.NaT

# Vendas/Pipeline: filtra por DATA DO EVENTO (Agenda), nao pelo codigo do projeto
if mes_sel != "Todos":
    m_num_kpi = meses_opts.index(mes_sel)
    vendas_filt = projetos[(projetos["_data_ev"].dt.year == ano)
                           & (projetos["_data_ev"].dt.month == m_num_kpi)]
else:
    vendas_filt = projetos[projetos["_data_ev"].dt.year == ano]

val_vendas = vendas_filt["Arrecad. Prevista (A)"].sum()
qtd_vendas = len(vendas_filt)
pipeline = vendas_filt["A Receber (C+D)"].sum()

periodo_lbl = f"{mes_sel}/{ano}" if mes_sel != "Todos" else str(ano)
margem = (lucro_real / faturamento * 100) if faturamento else 0
pct_soul = (desp_soul / despesas_total * 100) if despesas_total else 0
pct_ev = (desp_eventos / despesas_total * 100) if despesas_total else 0
label_per = f"{mes_sel}/{ano}" if mes_sel != "Todos" else str(ano)

# ====== BLOCO 1: PERFORMANCE (caixa) ======
st.markdown(f"#### 💰 Performance — {periodo_lbl}")
c1, c2, c3 = st.columns(3)
c1.metric("Faturamento (caixa)", brl(faturamento))
c2.metric("Despesas totais", brl(despesas_total))
c3.metric("Lucro Real", brl(lucro_real), f"{margem:.1f}% margem")

# ====== BLOCO 2: BREAKDOWN DESPESAS ======
st.markdown(f"#### 📂 Breakdown de Despesas — {periodo_lbl}")
d1, d2 = st.columns(2)
d1.metric("🏢 Operacional (Casa)", brl(desp_soul), f"{pct_soul:.1f}% do total")
d2.metric("🎪 Eventos", brl(desp_eventos), f"{pct_ev:.1f}% do total")

# ====== BLOCO 3: COMERCIAL ======
st.markdown(f"#### 📅 Pipeline Comercial — {label_per}")
v1, v2, v3 = st.columns(3)
v1.metric("Vendas", f"{qtd_vendas} eventos")
v2.metric("Valor contratado", brl(val_vendas))
v3.metric("Pipeline a receber", brl(pipeline))

st.divider()

tab1, tab2, tab4, tab_futuro = st.tabs(["📊 Painel", "🎪 Projetos", "📋 Lançamentos", "🔮 Futuro"])
# Variavel compartilhada entre abas: preparar pa_proj antes pra uso em tab2 e no sub_ano
pa_proj = projetos.copy()
pa_proj["data_evento"] = pd.to_datetime(pa_proj["data_evento_agenda"], errors="coerce")
pa_proj["Entrada Prevista"] = pd.to_numeric(pa_proj.get("Entrada Prevista"), errors="coerce").fillna(0)
pa_proj["Entrada Realizada"] = pd.to_numeric(pa_proj.get("Entrada Realizada"), errors="coerce").fillna(0)
pa_proj["Saída Realizada"] = pd.to_numeric(pa_proj.get("Saída Realizada"), errors="coerce").fillna(0)
pa_proj["Saída Prevista"] = pd.to_numeric(pa_proj.get("Saída Prevista"), errors="coerce").fillna(0)

with tab1:
    # ====== FLUXO MENSAL (gráfico dark moderno) ======
    st.markdown(f"### 💹 Fluxo de Caixa Mensal — {ano}")
    st.caption("Entradas (faturamento) vs Saídas (despesas pagas) · saldo acumulado")

    _r_fluxo = receber[receber["Data Pagamento"].dt.year == ano].dropna(subset=["Data Pagamento"]).copy()
    _r_fluxo["mes"] = _r_fluxo["Data Pagamento"].dt.to_period("M").astype(str)
    _entradas = _r_fluxo.groupby("mes")["Valor Pago"].sum()

    _p_fluxo = pagar[pagar["Pagamento"].dt.year == ano].dropna(subset=["Pagamento"]).copy()
    _p_fluxo["mes"] = _p_fluxo["Pagamento"].dt.to_period("M").astype(str)
    _cc_casa_f = ["Administrativo", "DP", "Comercial"]
    _saidas_casa = _p_fluxo[_p_fluxo["C. Custo"].isin(_cc_casa_f)].groupby("mes")["Valor Pagamento"].sum()
    _saidas_total = _p_fluxo.groupby("mes")["Valor Pagamento"].sum()

    _meses_f = sorted(set(_entradas.index) | set(_saidas_total.index))
    _entradas = _entradas.reindex(_meses_f, fill_value=0)
    _saidas_total = _saidas_total.reindex(_meses_f, fill_value=0)
    _saidas_casa = _saidas_casa.reindex(_meses_f, fill_value=0)
    _saidas_ev = _saidas_total - _saidas_casa
    _saldo = _entradas - _saidas_total
    _acum = _saldo.cumsum()

    _mesnames = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    _labels = [f"{_mesnames[int(m.split('-')[1])-1]}/{m.split('-')[0][2:]}" for m in _meses_f]

    fig_fluxo = go.Figure()
    fig_fluxo.add_trace(go.Bar(
        name="Entradas", x=_labels, y=_entradas.values,
        marker=dict(color="hsl(142, 71%, 45%)", line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Entradas: R$ %{y:,.0f}<extra></extra>",
    ))
    fig_fluxo.add_trace(go.Bar(
        name="Saídas Eventos", x=_labels, y=-_saidas_ev.values,
        marker=dict(color="#f97316", line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Saídas Eventos: R$ %{customdata:,.0f}<extra></extra>",
        customdata=_saidas_ev.values,
    ))
    fig_fluxo.add_trace(go.Bar(
        name="Saídas Casa", x=_labels, y=-_saidas_casa.values,
        marker=dict(color="hsl(0, 72%, 51%)", line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Saídas Casa: R$ %{customdata:,.0f}<extra></extra>",
        customdata=_saidas_casa.values,
    ))
    fig_fluxo.add_trace(go.Scatter(
        name="Saldo acumulado", x=_labels, y=_acum.values,
        mode="lines+markers",
        line=dict(color="hsl(45, 93%, 47%)", width=3),
        marker=dict(color="hsl(45, 93%, 47%)", size=10, line=dict(width=2, color="hsl(222, 47%, 11%)")),
        hovertemplate="<b>%{x}</b><br>Saldo acumulado: R$ %{y:,.2f}<extra></extra>",
    ))
    fig_fluxo.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="hsl(222, 47%, 14%)",
        barmode="relative",
        height=400,
        margin=dict(l=60, r=20, t=20, b=60),
        font=dict(color="#f1f5f9", size=13, family="Inter, sans-serif"),
        legend=dict(
            orientation="h", y=-0.2, x=0.5, xanchor="center",
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f1f5f9", size=14),
        ),
        xaxis=dict(showgrid=False, tickfont=dict(color="#f1f5f9", size=13)),
        yaxis=dict(
            gridcolor="hsl(217, 33%, 22%)", tickprefix="R$ ", tickformat=",.0f",
            zerolinecolor="hsl(217, 33%, 30%)", zerolinewidth=1,
            tickfont=dict(color="#f1f5f9", size=12),
        ),
        hoverlabel=dict(bgcolor="hsl(222, 47%, 14%)", bordercolor="hsl(45, 93%, 47%)",
                        font=dict(color="#f1f5f9", size=13)),
    )
    st.plotly_chart(fig_fluxo, use_container_width=True)

    st.markdown("---")
    st.markdown(f"### DRE hierárquico — {ano} (regime de caixa)")
    df = pagar_ano.dropna(subset=["grupo"]).copy()
    df["mes"] = df["data_ref"].dt.strftime("%m/%Y")

    # Receitas (caixa recebido)
    rec = receber_ano.dropna(subset=["Data Pagamento"]).copy()
    rec["mes"] = rec["Data Pagamento"].dt.strftime("%m/%Y")

    meses = sorted(set(df["mes"].dropna().unique()) | set(rec["mes"].dropna().unique()))

    rec_mes = rec.groupby("mes")["Valor Pago"].sum().reindex(meses, fill_value=0)
    desp_mes = df.groupby("mes")["valor_ref"].sum().reindex(meses, fill_value=0)
    resultado_mes = rec_mes - desp_mes

    rec_total = rec_mes.sum()
    desp_total = desp_mes.sum()
    resultado_total = rec_total - desp_total

    # Tabela HTML de Receitas/Despesas/Resultado (alinhamento perfeito)
    _h = "<table class='dre-table'><thead><tr><th style='text-align:left'>LINHA</th>"
    for m in meses:
        _h += f"<th>{m}</th>"
    _h += "<th>TOTAL</th></tr></thead><tbody>"

    # Receitas
    _h += "<tr><td style='text-align:left;font-weight:700'>🟢 RECEITAS (faturamento)</td>"
    for m in meses:
        _h += f"<td style='color:#2ecc71;font-weight:600'>{brl(rec_mes[m])}</td>"
    _h += f"<td style='color:#2ecc71;font-weight:700'>{brl(rec_total)}</td></tr>"

    # Despesas
    _h += "<tr><td style='text-align:left;font-weight:700'>🔴 DESPESAS (total)</td>"
    for m in meses:
        _h += f"<td style='color:#e74c3c;font-weight:600'>{brl(desp_mes[m])}</td>"
    _h += f"<td style='color:#e74c3c;font-weight:700'>{brl(desp_total)}</td></tr>"

    # Resultado
    _h += "<tr style='border-top:2px solid hsl(217,33%,30%)'><td style='text-align:left;font-weight:700'>💙 RESULTADO DO MÊS</td>"
    for m in meses:
        cor = "#2980b9" if resultado_mes[m] >= 0 else "#c0392b"
        _h += f"<td style='color:{cor};font-weight:700;font-size:15px'>{brl(resultado_mes[m])}</td>"
    cor = "#2980b9" if resultado_total >= 0 else "#c0392b"
    _h += f"<td style='color:{cor};font-weight:700;font-size:15px'>{brl(resultado_total)}</td></tr>"

    # Margem
    pct_tot = (resultado_total / rec_total * 100) if rec_total else 0
    _h += "<tr><td style='text-align:left;font-weight:600'>% Margem</td>"
    for m in meses:
        pct = (resultado_mes[m] / rec_mes[m] * 100) if rec_mes[m] else 0
        _h += f"<td>{pct:.1f}%</td>"
    _h += f"<td style='font-weight:700'>{pct_tot:.1f}%</td></tr>"

    _h += "</tbody></table>"
    st.markdown(_h, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Detalhamento das Despesas")

    # Le query params pra drill-down via click nos numeros
    qp = st.query_params
    if "drill_sub" in qp:
        st.session_state["drill_subgrupo"] = qp["drill_sub"]
        st.session_state["drill_grupo"] = qp.get("drill_grp", "")
        st.session_state["drill_mes_auto"] = qp.get("drill_mes", "Todos")
        st.session_state["drill_categoria"] = qp.get("drill_cat", "")
        st.query_params.clear()

    # CSS tabela DRE (estilo Nibo: 3 niveis)
    st.markdown("""
    <style>
      .dre-table { width: 100%; border-collapse: collapse; margin: 16px 0; font-variant-numeric: tabular-nums; }
      .dre-table th { text-align: right; padding: 10px 16px; font-weight: 700; color: hsl(210, 40%, 98%); font-size: 14px; border-bottom: 2px solid hsl(217, 33%, 22%); }
      .dre-table th:first-child { text-align: left; }
      .dre-table td { padding: 6px 8px; text-align: right; border-bottom: 1px solid hsl(217, 33%, 22%); color: hsl(210, 40%, 98%); font-size: 13px; white-space: nowrap; }
      .dre-table td:first-child { text-align: left; white-space: normal; }
      .dre-table th { white-space: nowrap; padding: 8px 8px; font-size: 13px; }
      /* Grupo (nível 1) */
      .dre-table .group-row td { font-weight: 700; font-size: 16px; background: hsl(222, 47%, 17%); }
      .dre-table .group-row td:last-child { color: hsl(45, 93%, 47%); }
      /* Subgrupo (nível 2) */
      .dre-table .sub-row td:first-child { padding-left: 24px; font-weight: 600; color: hsl(210, 40%, 98%); }
      .dre-table .sub-row td { background: hsl(222, 47%, 15%); font-weight: 600; }
      .dre-table .sub-row td:last-child { font-weight: 700; }
      /* Categoria (nível 3) */
      .dre-table .cat-row td:first-child { padding-left: 48px; color: hsl(215, 20%, 65%); font-weight: 400; font-size: 13px; }
      .dre-table .cat-row td { font-size: 14px; color: hsl(215, 20%, 75%); }
      .dre-table .cat-row:hover td { background: hsl(217, 33%, 17%); }
      .dre-table a { color: inherit; text-decoration: none; display: block; white-space: nowrap; }
      .dre-table a:hover { color: hsl(45, 93%, 47%) !important; cursor: pointer; }
      /* Scroll horizontal quando muitas colunas */
      [data-testid="stExpander"] > div > div { overflow-x: auto; }
    </style>
    """, unsafe_allow_html=True)

    import urllib.parse as _up

    def _lnk(texto, sub, grp, mes_label, cat=""):
        params = {"drill_sub": sub, "drill_grp": grp, "drill_mes": mes_label}
        if cat:
            params["drill_cat"] = cat
        qs = _up.urlencode(params)
        return f"<a href='?{qs}' target='_self'>{texto}</a>"

    # Ordem dos grupos de nivel 1 (Eventos primeiro, depois Operacionais)
    GRUPO_ORDER = ["DESPESAS COM EVENTOS", "DESPESAS OPERACIONAIS"]
    SUB_ORDER = ["DESPESAS FIXAS", "DESPESAS VARIÁVEIS", "DESPESAS TERCEIROS"]

    grupos_existentes = [g for g in GRUPO_ORDER if g in df["grupo"].dropna().unique()]
    for grupo in grupos_existentes:
        dfg = df[df["grupo"] == grupo]
        tot_g_mes = dfg.groupby("mes")["valor_ref"].sum().reindex(meses, fill_value=0)
        tot_g = tot_g_mes.sum()

        with st.expander(f"📂 **{grupo}**  —  {brl(tot_g)}", expanded=True):
            html = "<table class='dre-table'><thead><tr><th></th>"
            for m in meses:
                html += f"<th>{m}</th>"
            html += "<th>TOTAL</th></tr></thead><tbody>"

            # linha grupo (nivel 1)
            html += f"<tr class='group-row'><td>{grupo}</td>"
            for m in meses:
                html += f"<td>{brl(tot_g_mes[m])}</td>"
            html += f"<td>{brl(tot_g)}</td></tr>"

            if grupo == "DESPESAS COM EVENTOS":
                # Grupo EVENTOS: pula nivel 2, vai direto pras Categorias do SGE
                dfc = dfg.dropna(subset=["Categoria"])
                cats = sorted(dfc["Categoria"].unique())
                for cat in cats:
                    dfi = dfc[dfc["Categoria"] == cat]
                    tot_c_mes = dfi.groupby("mes")["valor_ref"].sum().reindex(meses, fill_value=0)
                    tot_c = tot_c_mes.sum()
                    if tot_c == 0:
                        continue
                    cat_short = cat if len(cat) <= 45 else cat[:42] + "..."
                    # usa a classe sub-row pq aqui eh nivel 2 visualmente
                    html += f"<tr class='sub-row'><td>{_lnk(cat_short, 'DESPESAS COM EVENTOS', grupo, 'Todos', cat)}</td>"
                    for m in meses:
                        v = tot_c_mes[m]
                        txt = brl(v) if v != 0 else "-"
                        if v != 0:
                            mm = int(m.split("/")[0])
                            mes_label = meses_opts[mm]
                            html += f"<td>{_lnk(txt, 'DESPESAS COM EVENTOS', grupo, mes_label, cat)}</td>"
                        else:
                            html += f"<td>{txt}</td>"
                    html += f"<td>{_lnk(brl(tot_c), 'DESPESAS COM EVENTOS', grupo, 'Todos', cat)}</td></tr>"
            else:
                # Grupo OPERACIONAIS: Subgrupo > Categoria (3 niveis)
                subs_existentes = [s for s in SUB_ORDER if s in dfg["subgrupo"].dropna().unique()]
                for sub in subs_existentes:
                    dfs = dfg[dfg["subgrupo"] == sub]
                    tot_s_mes = dfs.groupby("mes")["valor_ref"].sum().reindex(meses, fill_value=0)
                    tot_s = tot_s_mes.sum()
                    html += f"<tr class='sub-row'><td>{_lnk(sub, sub, grupo, 'Todos')}</td>"
                    for m in meses:
                        mm = int(m.split('/')[0])
                        mes_label = meses_opts[mm]
                        html += f"<td>{_lnk(brl(tot_s_mes[m]), sub, grupo, mes_label)}</td>"
                    html += f"<td>{_lnk(brl(tot_s), sub, grupo, 'Todos')}</td></tr>"

                    dfc = dfs.dropna(subset=["Categoria"])
                    cats = sorted(dfc["Categoria"].unique())
                    for cat in cats:
                        dfi = dfc[dfc["Categoria"] == cat]
                        tot_c_mes = dfi.groupby("mes")["valor_ref"].sum().reindex(meses, fill_value=0)
                        tot_c = tot_c_mes.sum()
                        if tot_c == 0:
                            continue
                        cat_short = cat if len(cat) <= 38 else cat[:35] + "..."
                        html += f"<tr class='cat-row'><td>{_lnk(f'↓ {cat_short}', sub, grupo, 'Todos', cat)}</td>"
                        for m in meses:
                            v = tot_c_mes[m]
                            txt = brl(v) if v != 0 else "-"
                            if v != 0:
                                mm = int(m.split("/")[0])
                                mes_label = meses_opts[mm]
                                html += f"<td>{_lnk(txt, sub, grupo, mes_label, cat)}</td>"
                            else:
                                html += f"<td>{txt}</td>"
                        html += f"<td>{_lnk(brl(tot_c), sub, grupo, 'Todos', cat)}</td></tr>"

            html += "</tbody></table>"
            st.markdown(html, unsafe_allow_html=True)

    # ==== SECAO DRILL (abre abaixo quando clica num subgrupo ou categoria) ====
    if st.session_state.get("drill_subgrupo"):
        sub_sel = st.session_state["drill_subgrupo"]
        grp_sel = st.session_state["drill_grupo"]
        cat_sel = st.session_state.get("drill_categoria", "")
        st.markdown("---")
        titulo = f"## 📋 Lançamentos — {sub_sel}"
        if cat_sel:
            titulo += f" › {cat_sel}"
        titulo += f"  ·  {ano}"
        col_h1, col_h2 = st.columns([6, 1])
        col_h1.markdown(titulo)
        if col_h2.button("❌ Fechar", key="fechar_drill"):
            st.session_state["drill_subgrupo"] = None
            st.session_state["drill_categoria"] = ""
            st.rerun()

        # Base: ano inteiro
        base = pagar[pagar["data_ref"].dt.year == ano].copy()
        base = base[base["subgrupo"] == sub_sel]
        if cat_sel:
            base = base[base["Categoria"] == cat_sel]

        # Filtros locais (mes auto-selecionado se veio de click numa coluna mensal)
        mes_default = st.session_state.get("drill_mes_auto", "Todos")
        if "mes_drill" not in st.session_state or st.session_state.get("_drill_mes_dirty") != sub_sel:
            st.session_state["mes_drill"] = mes_default
            st.session_state["_drill_mes_dirty"] = sub_sel

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            mes_drill = st.selectbox("Mês", meses_opts, key="mes_drill")
        with fc2:
            forn_drill = st.text_input("Fornecedor contém", key="forn_drill")
        with fc3:
            status_drill = st.selectbox("Status", ["Todos", "Pagos", "Em aberto"], key="status_drill")

        if mes_drill != "Todos":
            mn = meses_opts.index(mes_drill)
            base = base[base["data_ref"].dt.month == mn]
        if forn_drill:
            base = base[base["Fornecedor"].astype(str).str.contains(forn_drill, case=False, na=False)]
        if status_drill == "Pagos":
            base = base[base["Pagamento"].notna()]
        elif status_drill == "Em aberto":
            base = base[base["Pagamento"].isna()]

        cols_l = ["data_ref", "Fornecedor", "Descrição", "Serviço",
                  "Categoria", "C. Custo", "Conta Origem", "Projeto", "valor_ref"]
        cols_l = [c for c in cols_l if c in base.columns]
        show = base[cols_l].copy().sort_values("data_ref", ascending=False)
        show = show.rename(columns={
            "data_ref": "Pagamento", "Fornecedor": "Nome", "Serviço": "Ref",
            "C. Custo": "Centro de custo", "Conta Origem": "Conta",
            "valor_ref": "Valor pago",
        })
        if "Pagamento" in show.columns:
            show["Pagamento"] = show["Pagamento"].dt.strftime("%d/%m/%Y").fillna("-")
        total_sub = base["valor_ref"].sum()
        if "Valor pago" in show.columns:
            show["Valor pago"] = show["Valor pago"].apply(brl)

        st.markdown(f"**{len(base)} lançamentos · Total: {brl(total_sub)}**")
        st.dataframe(show, use_container_width=True, hide_index=True, height=500)

    st.markdown("---")
    by_grupo = df.groupby("grupo")["valor_ref"].sum().reset_index()
    fig = px.pie(by_grupo, values="valor_ref", names="grupo",
                 title=f"Distribuição de Despesas por Grupo em {ano}", hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### 🎪 Projetos — detalhe por evento")

    # Filtro por projeto (acima, independente de data)
    cod_filtro = st.text_input("🔍 Buscar por Nº Projeto", placeholder="ex: 0196/2025", key="cod_proj_filtro")

    # Filtros de período + custo
    sc1, sc2, sc3 = st.columns([1, 1, 2])
    with sc1:
        mes_ev = st.selectbox("Mês", list(range(0, 13)),
                               index=pd.Timestamp.today().month,
                               format_func=lambda m: "Todos" if m == 0 else meses_opts[m],
                               key="mes_proj_tab")
    with sc2:
        ano_ev = st.selectbox("Ano", [2026, 2027, 2025], key="ano_proj_tab")
    with sc3:
        pct_custo = st.slider("% Custo estimado do evento", 0, 100, 55,
                              key="pct_custo_proj_slider",
                              help="Percentual médio de custo sobre Entrada Prevista") / 100

    hoje = pd.Timestamp.today().normalize()

    # Filtro: se tem nº projeto, busca independente de data
    eventos_mes = pa_proj[pa_proj["Entrada Prevista"] > 0].copy()
    if cod_filtro.strip():
        eventos_mes = eventos_mes[eventos_mes["Projeto"].astype(str).str.contains(cod_filtro.strip(), case=False, na=False)]
    elif mes_ev == 0:
        eventos_mes = eventos_mes[eventos_mes["data_evento"].dt.year == ano_ev]
    else:
        eventos_mes = eventos_mes[
            (eventos_mes["data_evento"].dt.year == ano_ev)
            & (eventos_mes["data_evento"].dt.month == mes_ev)
        ]
    eventos_mes = eventos_mes.sort_values("data_evento")

    if len(eventos_mes) == 0:
        st.info("Nenhum projeto encontrado com esses filtros.")
    else:
        eventos_mes["Status"] = eventos_mes["data_evento"].apply(
            lambda d: "✅ Realizado" if pd.notna(d) and d < hoje else "🔜 A Realizar"
        )
        eventos_mes["A Receber Evento"] = eventos_mes["Entrada Prevista"] - eventos_mes["Entrada Realizada"]

        def _custo(row):
            if row["Status"] == "✅ Realizado":
                return row["Saída Realizada"]
            return row["Entrada Prevista"] * pct_custo

        def _lucro(row):
            if row["Status"] == "✅ Realizado":
                return row["Entrada Realizada"] - row["Saída Realizada"]
            return row["Entrada Prevista"] - (row["Entrada Prevista"] * pct_custo)

        def _liquidez(row):
            if row["Status"] == "✅ Realizado":
                return 0
            custo_est = row["Entrada Prevista"] * pct_custo
            desp_restante = max(0, custo_est - row["Saída Realizada"])
            return row["A Receber Evento"] - desp_restante

        eventos_mes["Custo"] = eventos_mes.apply(_custo, axis=1)
        eventos_mes["Lucro"] = eventos_mes.apply(_lucro, axis=1)
        eventos_mes["Liquidez Restante"] = eventos_mes.apply(_liquidez, axis=1)

        realizados_m = eventos_mes["Status"] == "✅ Realizado"
        futuros_m = ~realizados_m

        # KPIs
        tot_valor = eventos_mes["Entrada Prevista"].sum()
        tot_recebido = eventos_mes["Entrada Realizada"].sum()
        tot_receber = (eventos_mes["Entrada Prevista"] - eventos_mes["Entrada Realizada"]).clip(lower=0).sum()
        tot_despesa_eventos = eventos_mes["Custo"].sum()
        tot_lucro_evento = tot_valor - tot_despesa_eventos

        # Despesa Casa: real se mes passado especifico, media caso contrario
        cc_casa_ev = ["Administrativo", "DP", "Comercial"]
        if mes_ev > 0:
            mes_inicio = pd.Timestamp(ano_ev, mes_ev, 1)
            mes_fim = mes_inicio + pd.offsets.MonthEnd(0)
            if mes_fim < hoje:
                desp_casa = pagar[
                    pagar["Pagamento"].notna()
                    & (pagar["Pagamento"] >= mes_inicio) & (pagar["Pagamento"] <= mes_fim)
                    & pagar["C. Custo"].isin(cc_casa_ev)
                ]["Valor Pagamento"].sum()
                desp_casa_label = f"Despesa Casa ({meses_opts[mes_ev]}/{ano_ev})"
            else:
                _ma = pd.Timestamp(hoje.year, hoje.month, 1)
                _s = 0.0
                for _i in [1, 2, 3]:
                    _ms = _ma - pd.DateOffset(months=_i)
                    _me = _ms + pd.offsets.MonthEnd(0)
                    _s += pagar[
                        pagar["Pagamento"].notna()
                        & (pagar["Pagamento"] >= _ms) & (pagar["Pagamento"] <= _me)
                        & pagar["C. Custo"].isin(cc_casa_ev)
                    ]["Valor Pagamento"].sum()
                desp_casa = _s / 3
                desp_casa_label = "Despesa Casa (média 3m)"
        else:
            # Todos os meses: realizado (passado) + projeção (futuro)
            ano_ini = pd.Timestamp(ano_ev, 1, 1)
            mes_atual = pd.Timestamp(hoje.year, hoje.month, 1)

            # Realizado: meses já fechados (jan até mês anterior ao atual)
            desp_casa_real = pagar[
                pagar["Pagamento"].notna()
                & (pagar["Pagamento"] >= ano_ini) & (pagar["Pagamento"] < mes_atual)
                & pagar["C. Custo"].isin(cc_casa_ev)
            ]["Valor Pagamento"].sum()

            # Meses passados contados
            if ano_ev == hoje.year:
                meses_passados = hoje.month - 1  # jan até mes anterior
                meses_futuros = 12 - meses_passados
            elif ano_ev < hoje.year:
                meses_passados = 12
                meses_futuros = 0
            else:
                meses_passados = 0
                meses_futuros = 12

            # Média mensal dos últimos 3 meses (pra projetar futuro)
            _ma = pd.Timestamp(hoje.year, hoje.month, 1)
            _s_media = 0.0
            for _i in [1, 2, 3]:
                _ms = _ma - pd.DateOffset(months=_i)
                _me = _ms + pd.offsets.MonthEnd(0)
                _s_media += pagar[
                    pagar["Pagamento"].notna()
                    & (pagar["Pagamento"] >= _ms) & (pagar["Pagamento"] <= _me)
                    & pagar["C. Custo"].isin(cc_casa_ev)
                ]["Valor Pagamento"].sum()
            media_mensal = _s_media / 3

            # Projeção dos meses futuros
            desp_casa_proj = media_mensal * meses_futuros

            desp_casa = desp_casa_real + desp_casa_proj
            desp_casa_label = f"Despesa Casa ({ano_ev}: {meses_passados}m real + {meses_futuros}m projeção)"

        lucro_real_total = tot_lucro_evento - desp_casa
        qtd_r = realizados_m.sum()
        qtd_f = futuros_m.sum()

        periodo_txt = f"{meses_opts[mes_ev]} {ano_ev}" if mes_ev > 0 else f"{ano_ev}"
        st.markdown(f"## {periodo_txt}")
        st.caption(f"{qtd_r} realizado(s) · {qtd_f} a realizar · {len(eventos_mes)} projeto(s)")

        k1 = st.columns(4)
        k1[0].metric("💰 Valor Total (eventos)", brl(tot_valor))
        k1[1].metric("🟢 Recebido", brl(tot_recebido))
        k1[2].metric("🟡 A Receber", brl(tot_receber))
        k1[3].metric("🔴 Despesa Total (Eventos)", brl(tot_despesa_eventos))

        k2 = st.columns(3)
        k2[0].metric("🎯 Lucro Evento", brl(tot_lucro_evento),
                      f"{(tot_lucro_evento / tot_valor * 100):.1f}% margem" if tot_valor else "")
        k2[1].metric(f"🏢 {desp_casa_label}", brl(desp_casa))
        k2[2].metric("✨ Lucro Real", brl(lucro_real_total),
                      f"{(lucro_real_total / tot_valor * 100):.1f}% do Valor Total" if tot_valor else "")

        st.markdown("---")
        st.markdown("### 🎪 Projetos")

        # Cards por evento
        for _, ev in eventos_mes.iterrows():
            tipo_ev = ev.get("tipo_evento") or "Evento"
            desc = ev.get("Descrição Projeto")
            inst = ev.get("Instituição")
            cursos = ev.get("Cursos")
            if pd.notna(desc) and str(desc).strip():
                nome = str(desc).strip()
            else:
                partes = []
                if pd.notna(inst) and str(inst).strip():
                    partes.append(str(inst).strip())
                if pd.notna(cursos) and str(cursos).strip():
                    partes.append(str(cursos).strip())
                nome = " — ".join(partes) if partes else ev.get("Projeto")

            is_realizado = ev["Status"] == "✅ Realizado"
            data_str = ev["data_evento"].strftime("%d/%m/%Y") if pd.notna(ev["data_evento"]) else "-"
            pct_receb = min((ev["Entrada Realizada"] / ev["Entrada Prevista"] * 100) if ev["Entrada Prevista"] else 0, 100)
            bar_color = "hsl(142,71%,45%)" if pct_receb >= 80 else "hsl(45,93%,47%)" if pct_receb >= 50 else "hsl(0,72%,51%)"
            status_badge = "✅ Realizado" if is_realizado else "🔜 A Realizar"
            badge_bg = "hsl(142,71%,45%)" if is_realizado else "hsl(45,93%,47%)"
            badge_fg = "#fff" if is_realizado else "hsl(222,47%,11%)"

            # Header do card com tabela HTML (funciona no Streamlit)
            card_header = f"""
<table style='width:100%;border:none;border-collapse:collapse;'>
<tr><td style='border:none;padding:0;'>
    <span style='font-size:20px;font-weight:700;'>{ev['Projeto']}</span>
    <span style='background:{badge_bg};color:{badge_fg};padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;margin-left:8px;'>{status_badge}</span>
    <span style='background:hsl(217,33%,22%);color:hsl(215,20%,75%);padding:2px 8px;border-radius:6px;font-size:11px;margin-left:6px;'>{tipo_ev}</span>
</td><td style='border:none;padding:0;text-align:right;'>
    <span style='font-size:12px;color:hsl(215,20%,65%);'>Valor Total</span><br>
    <span style='font-size:26px;font-weight:800;'>{brl(ev['Entrada Prevista'])}</span>
</td></tr>
<tr><td colspan='2' style='border:none;padding:4px 0 0;font-size:15px;font-weight:500;'>{nome}</td></tr>
<tr><td colspan='2' style='border:none;padding:2px 0 8px;font-size:13px;color:hsl(215,20%,65%);'>📅 {data_str}</td></tr>
<tr><td colspan='2' style='border:none;padding:0;'>
    <table style='width:100%;border:none;border-collapse:collapse;margin-bottom:4px;'>
    <tr><td style='border:none;padding:0;font-size:12px;color:hsl(215,20%,65%);'>Recebido: {brl(ev['Entrada Realizada'])}</td>
        <td style='border:none;padding:0;text-align:right;font-size:12px;color:hsl(215,20%,65%);'>{pct_receb:.0f}%</td></tr></table>
    <div style='background:hsl(217,33%,22%);border-radius:6px;height:8px;overflow:hidden;'>
        <div style='background:{bar_color};height:100%;width:{pct_receb:.0f}%;border-radius:6px;'></div>
    </div>
</td></tr>
</table>"""

            with st.expander(f"{ev['Projeto']} · {status_badge} · {tipo_ev} · {brl(ev['Entrada Prevista'])}", expanded=False):
                st.markdown(card_header, unsafe_allow_html=True)

                m1, m2, m3 = st.columns(3)
                if not is_realizado:
                    m1.metric("🟡 A Receber", brl(ev["A Receber Evento"]))
                m2.metric("🔴 Despesas Realizadas", brl(ev["Saída Realizada"]))
                m3.metric("🟢 Recebido", brl(ev["Entrada Realizada"]))

                if is_realizado:
                    lucro_ev = ev["Entrada Realizada"] - ev["Saída Realizada"]
                    margem = (lucro_ev / ev["Entrada Realizada"] * 100) if ev["Entrada Realizada"] else 0
                    r1, r2 = st.columns(2)
                    r1.metric("💰 Lucro Real", brl(lucro_ev))
                    r2.metric("📊 Margem", f"{margem:.1f}%")
                else:
                    r1, r2, r3 = st.columns(3)
                    r1.metric(f"Custo Est. ({int(pct_custo*100)}%)", brl(ev["Custo"]))
                    r2.metric("Liquidez Restante", brl(ev["Liquidez Restante"]))
                    r3.metric("💰 Lucro Estimado", brl(ev["Lucro"]))

with tab4:
    st.markdown(f"### 📋 Lançamentos detalhados — {periodo_lbl}")
    st.caption("Filtro Ano/Mês usa o seletor do topo · usa data de pagamento (regime de caixa)")
    tipo = st.radio("Tipo", ["Contas a Pagar", "Contas a Receber"], horizontal=True)

    if tipo == "Contas a Pagar":
        # pagar_ano ja filtrado por ano+mes no topo
        df = pagar_ano.copy()
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            grupos = ["Todos"] + sorted(df["grupo"].dropna().unique().tolist())
            g_sel = st.selectbox("Grupo", grupos)
        with fc2:
            subs = ["Todos"] + sorted(df["subgrupo"].dropna().unique().tolist())
            s_sel = st.selectbox("Subgrupo", subs)
        with fc3:
            forn = st.text_input("Fornecedor contém", "")
        with fc4:
            status = st.selectbox("Status", ["Todos", "Pagos", "Em aberto"])

        if g_sel != "Todos":
            df = df[df["grupo"] == g_sel]
        if s_sel != "Todos":
            df = df[df["subgrupo"] == s_sel]
        if forn:
            df = df[df["Fornecedor"].astype(str).str.contains(forn, case=False, na=False)]
        if status == "Pagos":
            df = df[df["Pagamento"].notna()]
        elif status == "Em aberto":
            df = df[df["Pagamento"].isna()]

        st.markdown(f"**{len(df)} lançamentos · Total: {brl(df['valor_ref'].sum())}**")

        cols = ["data_ref", "Vencimento", "Pagamento", "Fornecedor", "Descrição",
                "Serviço", "grupo", "subgrupo", "Projeto", "Valor Parcela", "Valor Pagamento"]
        cols = [c for c in cols if c in df.columns]
        show = df[cols].copy().sort_values("data_ref", ascending=False)
        show = show.rename(columns={"data_ref": "Data"})
        for c in ("Data", "Vencimento", "Pagamento"):
            if c in show.columns:
                show[c] = show[c].dt.strftime("%d/%m/%Y").fillna("-")
        for c in ("Valor Parcela", "Valor Pagamento"):
            if c in show.columns:
                show[c] = show[c].apply(brl)
        st.dataframe(show, use_container_width=True, hide_index=True, height=500)

    else:  # Contas a Receber (recebidas + em aberto)
        fc1, fc2, fc3, fc4, fc5 = st.columns(5)
        with fc1:
            ano_cr = st.selectbox("Ano", [2026, 2025, 2024], key="ano_cr_lanc")
        with fc2:
            mes_cr = st.selectbox("Mês", meses_opts, key="mes_cr_lanc")
        with fc3:
            status_cr = st.selectbox("Status", ["Recebidos", "A receber", "Todos"], key="status_cr_lanc")
        with fc4:
            pagador = st.text_input("Pagador contém", "")
        with fc5:
            if status_cr == "Recebidos":
                meio_opts = ["Todos"] + sorted(receber["Meio de Pag."].dropna().unique().tolist())
            else:
                meio_opts = ["Todos"]
            m_sel = st.selectbox("Meio de pagamento", meio_opts)

        if status_cr == "A receber":
            # Parcelas em aberto (nao recebidas)
            df = nao_recebidas.copy()
            df = df[df["Data Vencimento"].dt.year == ano_cr]
            if mes_cr != "Todos":
                m_num_cr = meses_opts.index(mes_cr)
                df = df[df["Data Vencimento"].dt.month == m_num_cr]
            if pagador:
                df = df[df["Pagador"].astype(str).str.contains(pagador, case=False, na=False)]

            st.markdown(f"**{len(df)} parcelas em aberto · Valor total: {brl(df['Valor'].sum())}**")
            cols = ["Data Vencimento", "Projeto", "Nome", "Pagador", "Valor", "Meio de Pag."]
            cols = [c for c in cols if c in df.columns]
            show = df[cols].copy().sort_values("Data Vencimento", ascending=True)
            if "Data Vencimento" in show.columns:
                show["Data Vencimento"] = show["Data Vencimento"].dt.strftime("%d/%m/%Y").fillna("-")
            if "Valor" in show.columns:
                show["Valor"] = show["Valor"].apply(brl)
            st.dataframe(show, use_container_width=True, hide_index=True, height=500)

        else:
            # Recebidos (ou Todos = recebidos, já que não mescla com em aberto)
            df = receber.copy()
            df = df[df["Data Pagamento"].dt.year == ano_cr]
            if mes_cr != "Todos":
                m_num_cr = meses_opts.index(mes_cr)
                df = df[df["Data Pagamento"].dt.month == m_num_cr]
            if pagador:
                df = df[df["Pagador"].astype(str).str.contains(pagador, case=False, na=False)]
            if m_sel != "Todos":
                df = df[df["Meio de Pag."] == m_sel]

            st.markdown(f"**{len(df)} lançamentos · Valor: {brl(df['Valor'].sum())} · Pago: {brl(df['Valor Pago'].sum())}**")
            cols = ["Data Vencimento", "Data Pagamento", "Data Crédito", "Projeto", "Nome", "Pagador",
                    "Valor", "Valor Pago", "Meio de Pag."]
            cols = [c for c in cols if c in df.columns]
            show = df[cols].copy().sort_values("Data Pagamento", ascending=False)
            for c in ("Data Vencimento", "Data Pagamento", "Data Crédito"):
                if c in show.columns:
                    show[c] = show[c].dt.strftime("%d/%m/%Y").fillna("-")
            for c in ("Valor", "Valor Pago"):
                if c in show.columns:
                    show[c] = show[c].apply(brl)
            st.dataframe(show, use_container_width=True, hide_index=True, height=500)

# ========================================================================
# TAB FUTURO: 3 sub-abas consolidadas
# ========================================================================
with tab_futuro:
    st.markdown("### 📈 Projeção de Liquidez — próximos 6 meses")
    st.caption("Entradas previstas × Saídas previstas · calcula quanto Soul terá em caixa mês a mês")

    # ============ Saldo inicial (editável) ============
    st.markdown("#### 💳 Saldo bancário atual (edite se precisar)")
    sc = st.columns(5)
    s_rede = sc[0].number_input("Rede", value=5000.0, step=1000.0, key="s_rede", format="%.2f")
    s_brad = sc[1].number_input("Bradesco", value=164192.0, step=1000.0, key="s_brad", format="%.2f")
    s_itau = sc[2].number_input("Itaú", value=10000.0, step=1000.0, key="s_itau", format="%.2f")
    s_val = sc[3].number_input("Valore", value=21469.0, step=1000.0, key="s_val", format="%.2f")
    s_sgp = sc[4].number_input("SGP", value=13360.32, step=1000.0, key="s_sgp", format="%.2f")
    saldo_bancos = s_rede + s_brad + s_itau + s_val + s_sgp

    st.markdown("#### 💼 Saldo Conta Investimentos atual (edite se precisar)")
    ic = st.columns(1)
    s_xp = ic[0].number_input("XP Investimentos", value=1224591.96, step=1000.0, key="s_xp", format="%.2f")
    saldo_investimentos = s_xp

    saldo_inicial = saldo_bancos + saldo_investimentos

    # Cards totais
    st.markdown(
        f"""
        <div style='display:flex; gap:16px; margin:16px 0;'>
            <div style='flex:1; background:hsl(222,47%,14%); border:1px solid hsl(217,33%,22%); border-radius:12px; padding:16px 20px;'>
                <div style='color:hsl(215,20%,65%); font-size:13px;'>🏦 Saldo Bancos</div>
                <div style='color:hsl(210,40%,98%); font-size:24px; font-weight:700; margin-top:4px;'>{brl(saldo_bancos)}</div>
            </div>
            <div style='flex:1; background:hsl(222,47%,14%); border:1px solid hsl(217,33%,22%); border-radius:12px; padding:16px 20px;'>
                <div style='color:hsl(215,20%,65%); font-size:13px;'>💼 Saldo Investimentos</div>
                <div style='color:hsl(210,40%,98%); font-size:24px; font-weight:700; margin-top:4px;'>{brl(saldo_investimentos)}</div>
            </div>
            <div style='flex:1.2; background:linear-gradient(135deg,hsl(222,47%,14%),hsl(222,47%,17%)); border:1px solid hsl(45,93%,47%); border-radius:12px; padding:16px 20px;'>
                <div style='color:hsl(215,20%,65%); font-size:13px;'>💰 PATRIMÔNIO TOTAL</div>
                <div style='color:hsl(215,20%,65%); font-size:11px; margin-top:2px;'>Bancos + Investimentos</div>
                <div style='color:hsl(45,93%,47%); font-size:32px; font-weight:800; margin-top:4px;'>{brl(saldo_inicial)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ============ Entradas Previstas (PIPELINE REAL: parcelas em aberto por vencimento + Data Crédito futura) ============
    hoje = pd.Timestamp.today().normalize()
    _meses_restantes = 12 - hoje.month + 1
    fim_horizonte = pd.Timestamp(hoje.year, 12, 31)
    meses_fut_pr = pd.period_range(hoje, periods=_meses_restantes, freq="M").astype(str).tolist()

    # Premissas
    st.markdown("#### ⚙️ Premissas da projeção")
    _pr1, _pr2 = st.columns(2)
    with _pr1:
        st.markdown("**Receita:** parcelas em aberto agrupadas por vencimento + créditos futuros de cartão")
    with _pr2:
        pct_custo_proj = st.number_input("% Custo estimado", min_value=0, max_value=100, value=55, step=5,
                                        key="pct_custo_proj",
                                        help="Usado pra estimar saídas variáveis dos eventos sem despesa cadastrada") / 100

    entradas_por_mes = {m: 0.0 for m in meses_fut_pr}

    # FONTE 1: Contas NÃO Recebidas (parcelas em aberto, por Data Vencimento)
    parcelas_aberto = 0
    valor_aberto = 0.0
    if not nao_recebidas.empty:
        nr = nao_recebidas[
            nao_recebidas["Data Vencimento"].notna()
            & (nao_recebidas["Data Vencimento"] >= hoje)
            & (nao_recebidas["Data Vencimento"] <= fim_horizonte)
        ].copy()
        nr["mes"] = nr["Data Vencimento"].dt.to_period("M").astype(str)
        nr_por_mes = nr.groupby("mes")["Valor"].sum()
        for m, v in nr_por_mes.items():
            if m in entradas_por_mes:
                entradas_por_mes[m] += v
        parcelas_aberto = len(nr)
        valor_aberto = nr["Valor"].sum()

    # FONTE 2: Data Crédito futura (parcelas JÁ PAGAS pelo cliente, crédito pendente no banco)
    creditos_futuros = 0
    valor_creditos = 0.0
    cr_futuro = receber[
        receber["Data Crédito"].notna()
        & (receber["Data Crédito"] > hoje)
        & (receber["Data Crédito"] <= fim_horizonte)
    ].copy()
    if len(cr_futuro):
        cr_futuro["mes"] = cr_futuro["Data Crédito"].dt.to_period("M").astype(str)
        cr_por_mes = cr_futuro.groupby("mes")["Valor Pago"].sum()
        for m, v in cr_por_mes.items():
            if m in entradas_por_mes:
                entradas_por_mes[m] += v
        creditos_futuros = len(cr_futuro)
        valor_creditos = cr_futuro["Valor Pago"].sum()

    # Parcelas em atraso (vencidas e não pagas)
    parcelas_atraso = 0
    valor_atraso = 0.0
    if not nao_recebidas.empty:
        atraso = nao_recebidas[
            nao_recebidas["Data Vencimento"].notna()
            & (nao_recebidas["Data Vencimento"] < hoje)
        ]
        parcelas_atraso = len(atraso)
        valor_atraso = atraso["Valor"].sum()
        entradas_por_mes[meses_fut_pr[0]] += valor_atraso

    entradas_futuras = pd.Series(entradas_por_mes)

    # ============ Saídas FIXAS da Soul (Admin + Pessoal + Fixas — recorrentes) ============
    tres_meses_atras = hoje - pd.DateOffset(months=3)
    # Despesa da Casa = media dos 3 MESES INTEIROS anteriores (Jan, Fev, Mar se hoje eh Abr)
    cc_casa_3m = ["Administrativo", "DP", "Comercial"]
    _hoje = pd.Timestamp.today().normalize()
    _mes_atual_start = pd.Timestamp(_hoje.year, _hoje.month, 1)
    _soma = 0.0
    for _i in [1, 2, 3]:
        _m_start = _mes_atual_start - pd.DateOffset(months=_i)
        _m_end = _m_start + pd.offsets.MonthEnd(0)
        _soma += pagar[
            pagar["Pagamento"].notna()
            & (pagar["Pagamento"] >= _m_start)
            & (pagar["Pagamento"] <= _m_end)
            & pagar["C. Custo"].isin(cc_casa_3m)
        ]["Valor Pagamento"].sum()
    saida_fixa_mensal = _soma / 3 if _soma > 0 else 50000

    # ============ Saídas VARIÁVEIS por evento ============
    # Usa Saída Prevista se confiavel (>10% da Entrada), senão estima com % custo
    saidas_variaveis_mes = {m: 0.0 for m in meses_fut_pr}
    for _, r in pa_proj.iterrows():
        saida_prev = r.get("Saída Prevista", 0) or 0
        saida_real = r.get("Saída Realizada", 0) or 0
        entrada_prev = r.get("Entrada Prevista", 0) or 0

        # Se Saída Prevista é confiável (>10% da receita), usa ela
        if saida_prev > 0 and entrada_prev > 0 and (saida_prev / entrada_prev) > 0.10:
            a_pagar = saida_prev - saida_real
        elif entrada_prev > 0:
            a_pagar = (entrada_prev * pct_custo_proj) - saida_real
        else:
            continue
        if a_pagar <= 0:
            continue
        data_ev = r.get("data_evento")
        if pd.isna(data_ev) or data_ev > fim_horizonte:
            continue
        if data_ev < hoje:
            saidas_variaveis_mes[meses_fut_pr[0]] += a_pagar
            continue
        mes_ev = data_ev.strftime("%Y-%m")
        if mes_ev in saidas_variaveis_mes:
            saidas_variaveis_mes[mes_ev] += a_pagar

    saidas_futuras = pd.Series(saidas_variaveis_mes)
    despesa_mensal_media = saida_fixa_mensal

    st.markdown(f"**🎯 Saída fixa mensal (Casa):** {brl(saida_fixa_mensal)} *(média 3 meses)*")
    st.markdown(f"**🎯 Custo estimado dos eventos:** {int(pct_custo_proj*100)}% *(usado quando SGE não tem Saída Prevista)*")

    c_info = st.columns(4)
    c_info[0].metric("📋 Parcelas em aberto", f"{parcelas_aberto}", f"{brl(valor_aberto)}")
    c_info[1].metric("💳 Créditos futuros (cartão)", f"{creditos_futuros}", f"{brl(valor_creditos)}")
    c_info[2].metric("⚠️ Parcelas em atraso", f"{parcelas_atraso}", f"{brl(valor_atraso)}")
    c_info[3].metric("💰 Total entradas previstas", brl(entradas_futuras.sum()))

    st.markdown("---")

    # ============ Tabela Projeção ============
    meses_fut = meses_fut_pr
    projecao = []
    saldo = saldo_inicial
    for m in meses_fut:
        e = entradas_futuras.get(m, 0)
        s_var = saidas_futuras.get(m, 0)
        s = saida_fixa_mensal + s_var  # fixa + variavel do evento
        saldo_final = saldo + e - s
        projecao.append({
            "Mês": m,
            "Saldo inicial": saldo,
            "Entradas previstas": e,
            "Saídas fixas": saida_fixa_mensal,
            "Saídas variáveis (eventos)": s_var,
            "Saídas previstas": s,
            "Saldo final": saldo_final,
            "Gap?": saldo_final < 0,
        })
        saldo = saldo_final

    df_proj = pd.DataFrame(projecao)

    # Tabela HTML (alinhamento perfeito, sem quebra)
    _th = "<table class='dre-table'><thead><tr>"
    for h in ["Mês", "Saldo inicial", "Entradas", "Saída Casa", "Saída Eventos", "Saída Total", "Saldo final", "Status"]:
        _th += f"<th>{h}</th>"
    _th += "</tr></thead><tbody>"
    for row in projecao:
        cor = "#c0392b" if row["Gap?"] else "#2980b9"
        if row["Gap?"]:
            status = "🚨 NEGATIVO"
        elif row["Saldo final"] < despesa_mensal_media * 0.5:
            status = "⚠️ Baixo"
        else:
            status = "✅ OK"
        _th += f"<tr>"
        _th += f"<td style='text-align:left;font-weight:700'>{row['Mês']}</td>"
        _th += f"<td>{brl(row['Saldo inicial'])}</td>"
        _th += f"<td style='color:#2ecc71'>{brl(row['Entradas previstas'])}</td>"
        _th += f"<td style='color:#e74c3c'>{brl(row['Saídas fixas'])}</td>"
        _th += f"<td style='color:#f97316'>{brl(row['Saídas variáveis (eventos)'])}</td>"
        _th += f"<td style='color:#e74c3c;font-weight:600'>{brl(row['Saídas previstas'])}</td>"
        _th += f"<td style='color:{cor};font-weight:700;font-size:15px'>{brl(row['Saldo final'])}</td>"
        _th += f"<td>{status}</td>"
        _th += "</tr>"
    _th += "</tbody></table>"
    st.markdown(_th, unsafe_allow_html=True)

    st.markdown("---")

    # ============ Gráfico da Projeção ============
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Entradas", x=df_proj["Mês"], y=df_proj["Entradas previstas"],
                         marker_color="#2ecc71"))
    fig.add_trace(go.Bar(name="Saídas", x=df_proj["Mês"], y=-df_proj["Saídas previstas"],
                         marker_color="#e74c3c"))
    fig.add_trace(go.Scatter(name="Saldo projetado", x=df_proj["Mês"], y=df_proj["Saldo final"],
                              mode="lines+markers", marker_color="#2980b9", line=dict(width=3),
                              yaxis="y"))
    fig.add_hline(y=despesa_mensal_media, line_dash="dash", line_color="orange",
                  annotation_text=f"Break-even ({brl(despesa_mensal_media)})")
    fig.add_hline(y=0, line_color="red")
    fig.update_layout(barmode="relative", title="Projeção de Caixa — 6 meses", height=450)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ============ Premissas ============
    with st.expander("📋 Premissas do cálculo"):
        st.markdown(f"""
        - **Saldo inicial**: soma dos 5 bancos (editável acima)
        - **Entradas previstas**: Contas a Receber do SGE com vencimento futuro e ainda não pagas
        - **Saídas previstas**: Contas a Pagar do SGE com vencimento futuro E a média de despesas dos últimos 3 meses (o maior dos dois)
        - **Break-even mensal**: {brl(despesa_mensal_media)} (média das despesas pagas nos últimos 3 meses)
        - **Horizonte**: {meses_fut[0]} até {meses_fut[-1]}
        - **Alerta 🚨**: saldo final negativo
        - **Alerta ⚠️**: saldo abaixo de 50% do break-even
        """)

    # ============ Dicas de ação ============
    gap_meses = [r for r in projecao if r["Gap?"]]
    if gap_meses:
        st.error(f"⚠️ **Atenção:** caixa fica negativo em {len(gap_meses)} mês(es): " +
                 ", ".join(r["Mês"] for r in gap_meses))
        primeiro_gap = gap_meses[0]
        necessidade = abs(primeiro_gap["Saldo final"])
        st.markdown(f"Pra não estourar em **{primeiro_gap['Mês']}**, você precisa:")
        st.markdown(f"- Receber **+{brl(necessidade)}** extras nesse mês, OU")
        st.markdown(f"- Reduzir **{brl(necessidade)}** de despesas, OU")
        st.markdown(f"- Fechar **{int(necessidade / 33000)} novos contratos** (ticket médio R$ 33K)")
    else:
        st.success("✅ Caixa projetado positivo nos próximos 6 meses.")
