"""
Rodar SÓ os arquivos que faltaram. Detecta login automaticamente.
Se sessão expirou, abre navegador — você loga — e o script detecta e continua sozinho.
"""
import sys
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE = "https://sistema.sge.com.br/SGE/Forms/"
HOJE = datetime.now().strftime("%d.%m.%Y")
PASTA = Path(rf"C:\Users\Laysa\Claude_Projetos\soul-festas-dashboard\ingest\data_raw\{HOJE}")
AUTH = Path("sge_auth.json")

def setar(page, id, val):
    page.evaluate(f"""() => {{
        const el = document.getElementById({id!r});
        if (el) {{
            el.value = {val!r};
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}
    }}""")

def download(page, acao, destino, desc, timeout=300_000):
    print(f"  → {desc}", flush=True)
    try:
        with page.expect_download(timeout=timeout) as dl:
            acao()
        dl.value.save_as(str(destino))
        print(f"    OK  {destino.name} ({destino.stat().st_size:,} bytes)", flush=True)
        return True
    except Exception as e:
        print(f"    ERRO {type(e).__name__}: {str(e)[:200]}", flush=True)
        return False

def try_export(page):
    """Depois de Pesquisar, procura botão Excel/Exportar."""
    page.wait_for_load_state("networkidle", timeout=60_000)
    page.wait_for_timeout(3000)
    achados = page.evaluate("""() => {
        return [...document.querySelectorAll('input, button, a, img')]
            .filter(el => {
                const t = (el.value || el.innerText || el.alt || el.title || '').toLowerCase();
                const id = (el.id || '').toLowerCase();
                return (t.includes('excel') || t.includes('planilha') || t.includes('exportar')
                        || id.includes('excel') || id.includes('exportar'))
                    && el.offsetParent !== null;
            })
            .map(el => ({id: el.id, text: (el.value||el.innerText||el.alt||'').trim().slice(0,60)}));
    }""")
    print(f"    (export cand: {len(achados)})", flush=True)
    for c in achados[:5]:
        print(f"      {c}", flush=True)
    for c in achados:
        if c["id"]:
            try:
                page.locator(f"#{c['id']}").click(timeout=5000)
                print(f"    (cliquei id={c['id']})", flush=True)
                return True
            except Exception:
                pass
    return False


def esperar_login(page, timeout_s=900):
    """Aguarda login. Detecta quando URL NÃO é mais tela de login."""
    print("\n>>> FAÇA O LOGIN no navegador que abriu.", flush=True)
    print(">>> Usuário: monique.rs2016@gmail.com  Senha: 09101979Db*", flush=True)
    print(">>> Estou detectando automaticamente. Aguardando ate 15 min...", flush=True)
    inicio = time.time()
    ultima_url = ""
    while time.time() - inicio < timeout_s:
        try:
            url = page.url.lower()
            if url != ultima_url:
                print(f"    (URL atual: {page.url})", flush=True)
                ultima_url = url
            # Considera logado se URL NÃO tem palavra de login
            if url and "login" not in url and "acesso" not in url and url != "about:blank":
                # Verificar se tem elemento típico de usuário logado
                try:
                    tem_btn_logout = page.locator("#ctl00_btnLogout, input[value*='Sair']").count() > 0
                    if tem_btn_logout:
                        print(f"    OK Login detectado (URL: {page.url})", flush=True)
                        return True
                except Exception:
                    pass
        except Exception as e:
            pass
        time.sleep(3)
    return False


def main():
    PASTA.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        if AUTH.exists():
            ctx = browser.new_context(storage_state=str(AUTH), accept_downloads=True)
            page = ctx.new_page()
            page.goto(BASE + "Agenda.aspx", wait_until="domcontentloaded", timeout=30_000)
            # Verificar se sessão ainda vale
            time.sleep(2)
            if "login" in page.url.lower():
                print("Sessão expirada. Aguardando novo login...", flush=True)
                if not esperar_login(page):
                    print("Login não detectado em 10min. Abortando.", flush=True)
                    return
                ctx.storage_state(path=str(AUTH))
                print(f"Sessão renovada salva em {AUTH}", flush=True)
        else:
            ctx = browser.new_context(accept_downloads=True)
            page = ctx.new_page()
            page.goto(BASE + "Agenda.aspx", timeout=30_000)
            if not esperar_login(page):
                print("Login não detectado em 10min. Abortando.", flush=True)
                return
            ctx.storage_state(path=str(AUTH))
            print(f"Sessão salva em {AUTH}", flush=True)

        page.set_default_timeout(60_000)

        try:
            # ============ 1. Contas a Receber NÃO PAGAS (CRÍTICO) ============
            print("\n[A] CONTAS A RECEBER — NÃO PAGAS", flush=True)
            page.goto(BASE + "ContasAReceber.aspx", wait_until="networkidle", timeout=90_000)
            page.wait_for_timeout(2000)
            page.select_option("#ctl00_cMain_ddlStatusCobranca", "A")
            for c in ["ctl00_cMain_txtDataInicio","ctl00_cMain_txtDataFim",
                      "ctl00_cMain_txtDataPagIni","ctl00_cMain_txtDataPagFim",
                      "ctl00_cMain_txtDataCredIni","ctl00_cMain_txtDataCredFim"]:
                setar(page, c, "")
            def a1():
                page.click("#ctl00_cMain_btnPesquisar")
                try_export(page)
            download(page, a1, PASTA / "Contas_nao_recebidas.xlsx", "C.Receber NÃO Pagas")

            # ============ 2. Contas a Receber PAGAS ============
            print("\n[B] CONTAS A RECEBER — PAGAS", flush=True)
            for de, ate, nome in [
                ("01/01/2025", "31/12/2025", "Contas_a_Receber_PAGAS_2025.xlsx"),
                ("01/01/2026", "31/12/2026", "Contas_a_Receber_PAGAS_2026.xlsx"),
            ]:
                page.goto(BASE + "ContasAReceber.aspx", wait_until="networkidle", timeout=90_000)
                page.wait_for_timeout(2000)
                page.select_option("#ctl00_cMain_ddlStatusCobranca", "P")
                setar(page, "ctl00_cMain_txtDataPagIni", de)
                setar(page, "ctl00_cMain_txtDataPagFim", ate)
                def a2():
                    page.click("#ctl00_cMain_btnPesquisar")
                    try_export(page)
                download(page, a2, PASTA / nome, f"C.Receber Pagas {de[-4:]}")

            # ============ 3. Contas a Pagar (4 arquivos) ============
            print("\n[C] CONTAS A PAGAR", flush=True)
            for de, ate, nome in [
                ("01/01/2025", "30/06/2025", "Contas_a_Pagar_1SEM2025.xlsx"),
                ("01/07/2025", "31/12/2025", "Contas_a_Pagar_2SEM2025.xlsx"),
                ("01/01/2026", "30/06/2026", "Contas_a_Pagar_1SEM2026.xlsx"),
                ("01/07/2026", "31/12/2026", "Contas_a_Pagar_2SEM2026.xlsx"),
            ]:
                page.goto(BASE + "ContaPagar.aspx", wait_until="networkidle", timeout=90_000)
                page.wait_for_timeout(2000)
                page.select_option("#ctl00_cMain_ddlStatus", "T")
                setar(page, "ctl00_cMain_txtDataVencIni", de)
                setar(page, "ctl00_cMain_txtDataVencFim", ate)
                def a3():
                    page.click("#ctl00_cMain_btnPesquisar")
                    try_export(page)
                download(page, a3, PASTA / nome, f"C.Pagar {de[-4:]} sem {de[3:5]}-{ate[3:5]}")

            # ============ 4. Inadimplentes ============
            print("\n[D] INADIMPLENTES", flush=True)
            page.goto(BASE + "Reports/RelClientesInadimplentes.aspx", wait_until="networkidle", timeout=90_000)
            page.wait_for_timeout(2000)
            page.select_option("#ctl00_cMain_ddlTipoRelatorio", "P")
            page.select_option("#ctl00_cMain_ddlStatusProjeto", "A")
            page.wait_for_timeout(1000)
            download(
                page,
                lambda: page.click("#ctl00_cMain_btnGerarRelatorio"),
                PASTA / "PlanilhaClientesInadimplentes.xlsx",
                "Inadimplentes",
                timeout=600_000,
            )

        except Exception as e:
            print(f"\nERRO GERAL: {type(e).__name__}: {str(e)[:300]}", flush=True)
        finally:
            print("\n" + "="*60, flush=True)
            print(f"CONFERÊNCIA — {PASTA}", flush=True)
            print("="*60, flush=True)
            esp = ["Contas_a_Pagar_1SEM2025.xlsx","Contas_a_Pagar_2SEM2025.xlsx",
                   "Contas_a_Pagar_1SEM2026.xlsx","Contas_a_Pagar_2SEM2026.xlsx",
                   "Contas_a_Receber_PAGAS_2025.xlsx","Contas_a_Receber_PAGAS_2026.xlsx",
                   "Contas_nao_recebidas.xlsx","AgendaResumida.xlsx",
                   "BalancoPorProjetoResumido.xlsx","CustoDoProjeto.xlsx",
                   "PlanilhaClientesInadimplentes.xlsx"]
            ok = 0
            for n in esp:
                p_ = PASTA / n
                if p_.exists() and p_.stat().st_size > 0:
                    print(f"  OK  {n} ({p_.stat().st_size:,} bytes)", flush=True)
                    ok += 1
                else:
                    print(f"  FALTOU  {n}", flush=True)
            print(f"\n  {ok}/{len(esp)} arquivos.", flush=True)
            browser.close()

if __name__ == "__main__":
    main()
