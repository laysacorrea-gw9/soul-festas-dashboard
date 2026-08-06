"""
================================================================================
SGE - Download automático dos 11 relatórios financeiros da Soul Festas
================================================================================
v3 (06/08/2026) — IDs corrigidos + datas via JS (bypassa accordions ocultos).

Requisitos:
    pip install playwright
    playwright install chromium

Rodar:
    python baixar_relatorios_sge.py
================================================================================
"""

import sys
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE = "https://sistema.sge.com.br/SGE/Forms/"
HOJE = datetime.now().strftime("%d.%m.%Y")
PASTA_DESTINO = Path(
    rf"C:\Users\Laysa\Claude_Projetos\soul-festas-dashboard\ingest\data_raw\{HOJE}"
)
AUTH_FILE = Path("sge_auth.json")
DOWNLOAD_TIMEOUT = 300_000


# ============================================================================
# HELPERS
# ============================================================================

def setar_valor(page, id_elemento, valor):
    """Seta valor via JS (bypassa problemas de visibilidade)."""
    page.evaluate(f"""() => {{
        const el = document.getElementById({id_elemento!r});
        if (el) {{
            el.value = {valor!r};
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}
    }}""")


def salvar_download(page, acao, destino: Path, descricao: str):
    """Executa 'acao' e salva o download em 'destino'."""
    print(f"  → {descricao}", flush=True)
    try:
        with page.expect_download(timeout=DOWNLOAD_TIMEOUT) as dl_info:
            acao()
        download = dl_info.value
        download.save_as(str(destino))
        tamanho = destino.stat().st_size
        print(f"    OK  Salvo: {destino.name} ({tamanho:,} bytes)", flush=True)
        return True
    except PWTimeout:
        print(f"    ERRO Timeout: {descricao}", flush=True)
        return False
    except Exception as e:
        print(f"    ERRO {type(e).__name__}: {e}", flush=True)
        return False


def tentar_clicar_export(page):
    """Depois de Pesquisar em Contas a Pagar/Receber, procura botão Excel/Exportar."""
    page.wait_for_load_state("networkidle", timeout=60_000)
    page.wait_for_timeout(2000)

    # Estratégia 1: seletores comuns
    candidatos = [
        "input[value*='Excel']",
        "input[value*='Planilha']",
        "input[value*='Exportar']",
        "button:has-text('Excel')",
        "button:has-text('Exportar')",
        "a:has-text('Excel')",
    ]
    for sel in candidatos:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible(timeout=500):
                loc.click()
                print(f"    (clicou em: {sel})", flush=True)
                return True
        except Exception:
            continue

    # Estratégia 2: buscar por qualquer elemento com "excel" no id/name/text
    encontrados = page.evaluate("""() => {
        return [...document.querySelectorAll('input, button, a, img')]
            .filter(el => {
                const t = (el.value || el.innerText || el.alt || el.title || '').toLowerCase();
                const id = (el.id || '').toLowerCase();
                const name = (el.name || '').toLowerCase();
                return t.includes('excel') || t.includes('exportar') || t.includes('planilha')
                    || id.includes('excel') || id.includes('exportexcel')
                    || name.includes('excel');
            })
            .map(el => ({
                tag: el.tagName,
                id: el.id,
                name: el.name,
                text: (el.value || el.innerText || el.alt || el.title || '').trim().slice(0, 80),
                visible: el.offsetParent !== null,
            }));
    }""")
    print(f"    (candidatos export encontrados: {len(encontrados)})", flush=True)
    for c in encontrados[:8]:
        print(f"      {c}", flush=True)

    # Tenta clicar no primeiro visível
    for c in encontrados:
        if c["visible"] and c["id"]:
            try:
                page.locator(f"#{c['id']}").click(timeout=3000)
                print(f"    (clicou id={c['id']!r})", flush=True)
                return True
            except Exception as e:
                print(f"    (falha clicar id={c['id']}: {e})", flush=True)
    return False


# ============================================================================
# RELATÓRIOS
# ============================================================================

def contas_a_pagar(page):
    print("\n[1] CONTAS A PAGAR (4 arquivos)", flush=True)
    semestres = [
        ("01/01/2025", "30/06/2025", "Contas_a_Pagar_1SEM2025.xlsx"),
        ("01/07/2025", "31/12/2025", "Contas_a_Pagar_2SEM2025.xlsx"),
        ("01/01/2026", "30/06/2026", "Contas_a_Pagar_1SEM2026.xlsx"),
        ("01/07/2026", "31/12/2026", "Contas_a_Pagar_2SEM2026.xlsx"),
    ]
    for de, ate, nome in semestres:
        page.goto(BASE + "ContaPagar.aspx", wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(1000)

        # Status = Pagas e Não Pagas (T)
        page.select_option("#ctl00_cMain_ddlStatus", "T")

        # Data Vencimento
        setar_valor(page, "ctl00_cMain_txtDataVencIni", de)
        setar_valor(page, "ctl00_cMain_txtDataVencFim", ate)

        # Pesquisar → Exportar
        def acao():
            page.click("#ctl00_cMain_btnPesquisar")
            tentar_clicar_export(page)

        salvar_download(page, acao, PASTA_DESTINO / nome, f"Contas a Pagar {de[-4:]} {de[:2]}-{ate[:2]}º sem")


def contas_a_receber_pagas(page):
    print("\n[2] CONTAS A RECEBER — PAGAS (2 arquivos)", flush=True)
    anos = [
        ("01/01/2025", "31/12/2025", "Contas_a_Receber_PAGAS_2025.xlsx"),
        ("01/01/2026", "31/12/2026", "Contas_a_Receber_PAGAS_2026.xlsx"),
    ]
    for de, ate, nome in anos:
        page.goto(BASE + "ContasAReceber.aspx", wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(1000)

        # Status Cobrança = Pagas (P)
        page.select_option("#ctl00_cMain_ddlStatusCobranca", "P")

        # Data Pagamento
        setar_valor(page, "ctl00_cMain_txtDataPagIni", de)
        setar_valor(page, "ctl00_cMain_txtDataPagFim", ate)

        def acao():
            page.click("#ctl00_cMain_btnPesquisar")
            tentar_clicar_export(page)

        salvar_download(page, acao, PASTA_DESTINO / nome, f"C.Receber PAGAS {de[-4:]}")


def contas_a_receber_nao_pagas(page):
    print("\n[3] CONTAS A RECEBER — NÃO PAGAS (1 arquivo)", flush=True)
    page.goto(BASE + "ContasAReceber.aspx", wait_until="networkidle", timeout=60_000)
    page.wait_for_timeout(1000)

    # Status = Não Pagas (A)
    page.select_option("#ctl00_cMain_ddlStatusCobranca", "A")

    # Limpar todas as datas (via JS)
    for campo in [
        "ctl00_cMain_txtDataInicio", "ctl00_cMain_txtDataFim",
        "ctl00_cMain_txtDataPagIni", "ctl00_cMain_txtDataPagFim",
        "ctl00_cMain_txtDataCredIni", "ctl00_cMain_txtDataCredFim",
    ]:
        setar_valor(page, campo, "")

    def acao():
        page.click("#ctl00_cMain_btnPesquisar")
        tentar_clicar_export(page)

    salvar_download(page, acao, PASTA_DESTINO / "Contas_nao_recebidas.xlsx", "C.Receber NÃO Pagas (datas branco)")


def agenda_resumida(page):
    print("\n[4] AGENDA RESUMIDA (1 arquivo)", flush=True)
    page.goto(BASE + "Reports/RelAgenda.aspx", wait_until="networkidle", timeout=60_000)

    page.select_option("#ctl00_cMain_ddlTipoRelatorio", "RP")

    # Tentar clicar accordion (pode ou não existir)
    try:
        page.click("text=PERÍODO DE REALIZAÇÃO DO EVENTO", timeout=3000)
    except Exception:
        pass
    page.wait_for_timeout(500)

    setar_valor(page, "ctl00_cMain_periodoEvento_txtDataIni", "01/01/2025")
    setar_valor(page, "ctl00_cMain_periodoEvento_txtDataFim", "31/12/2027")

    salvar_download(
        page,
        lambda: page.click("#ctl00_cMain_btnGerarRelatorio"),
        PASTA_DESTINO / "AgendaResumida.xlsx",
        "Agenda Resumida 2025-2027",
    )


def balanco_por_projeto(page):
    print("\n[5] BALANÇO POR PROJETO RESUMIDO (1 arquivo)", flush=True)
    page.goto(BASE + "Reports/RelBalancoDoContrato.aspx", wait_until="networkidle", timeout=60_000)

    page.select_option("#ctl00_cMain_ddlTipoRelatorio", "C")
    page.wait_for_timeout(500)

    salvar_download(
        page,
        lambda: page.click("#ctl00_cMain_btnGerarRelatorio"),
        PASTA_DESTINO / "BalancoPorProjetoResumido.xlsx",
        "Balanço por Projeto",
    )


def custo_do_projeto(page):
    print("\n[6] CUSTO DO PROJETO (1 arquivo)", flush=True)
    page.goto(BASE + "Reports/RelCustosDoProjeto.aspx", wait_until="networkidle", timeout=60_000)

    page.select_option("#ctl00_cMain_ddlTipo", "C")
    page.wait_for_timeout(500)

    salvar_download(
        page,
        lambda: page.click("#ctl00_cMain_btnGerarRelatorio"),
        PASTA_DESTINO / "CustoDoProjeto.xlsx",
        "Custo do Projeto",
    )


def inadimplentes(page):
    print("\n[7] PLANILHA CLIENTES INADIMPLENTES (1 arquivo)", flush=True)
    page.goto(BASE + "Reports/RelClientesInadimplentes.aspx", wait_until="networkidle", timeout=60_000)

    page.select_option("#ctl00_cMain_ddlTipoRelatorio", "P")
    page.select_option("#ctl00_cMain_ddlStatusProjeto", "A")
    page.wait_for_timeout(500)

    salvar_download(
        page,
        lambda: page.click("#ctl00_cMain_btnGerarRelatorio"),
        PASTA_DESTINO / "PlanilhaClientesInadimplentes.xlsx",
        "Clientes Inadimplentes",
    )


# ============================================================================
# CONFERÊNCIA + MAIN
# ============================================================================

ESPERADOS = [
    "Contas_a_Pagar_1SEM2025.xlsx", "Contas_a_Pagar_2SEM2025.xlsx",
    "Contas_a_Pagar_1SEM2026.xlsx", "Contas_a_Pagar_2SEM2026.xlsx",
    "Contas_a_Receber_PAGAS_2025.xlsx", "Contas_a_Receber_PAGAS_2026.xlsx",
    "Contas_nao_recebidas.xlsx",
    "AgendaResumida.xlsx",
    "BalancoPorProjetoResumido.xlsx",
    "CustoDoProjeto.xlsx",
    "PlanilhaClientesInadimplentes.xlsx",
]


def conferencia():
    print("\n" + "=" * 60, flush=True)
    print(f"CONFERÊNCIA — {PASTA_DESTINO}", flush=True)
    print("=" * 60, flush=True)
    ok = 0
    for nome in ESPERADOS:
        p = PASTA_DESTINO / nome
        if p.exists() and p.stat().st_size > 0:
            print(f"  OK  {nome} ({p.stat().st_size:,} bytes)", flush=True)
            ok += 1
        else:
            print(f"  FALTOU  {nome}", flush=True)
    print("-" * 60, flush=True)
    print(f"  {ok}/{len(ESPERADOS)} arquivos.", flush=True)


def main():
    PASTA_DESTINO.mkdir(parents=True, exist_ok=True)
    print(f"Pasta destino: {PASTA_DESTINO}", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        if AUTH_FILE.exists():
            context = browser.new_context(storage_state=str(AUTH_FILE), accept_downloads=True)
            page = context.new_page()
            print(f"OK Sessão carregada de {AUTH_FILE}", flush=True)
        else:
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.goto(BASE + "Agenda.aspx")
            print("\n>>> FAÇA LOGIN no navegador. Depois aperte ENTER aqui...", flush=True)
            input()
            context.storage_state(path=str(AUTH_FILE))

        try:
            # Ordem: começa pelos 4 fáceis (Gerar Relatório direto)
            agenda_resumida(page)
            balanco_por_projeto(page)
            custo_do_projeto(page)
            inadimplentes(page)
            # Depois os 3 que precisam Pesquisar + Exportar
            contas_a_receber_nao_pagas(page)
            contas_a_receber_pagas(page)
            contas_a_pagar(page)
        except Exception as e:
            print(f"\nERRO GERAL: {type(e).__name__}: {e}", flush=True)
        finally:
            conferencia()
            browser.close()


if __name__ == "__main__":
    main()
