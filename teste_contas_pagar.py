"""
Teste isolado: baixar Contas a Pagar 2026 1SEM e INSPECIONAR botões após Pesquisar.
"""
import sys
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

BASE = "https://sistema.sge.com.br/SGE/Forms/"
AUTH_FILE = Path("sge_auth.json")
HOJE = datetime.now().strftime("%d.%m.%Y")
PASTA = Path(rf"C:\Users\Laysa\Claude_Projetos\soul-festas-dashboard\ingest\data_raw\{HOJE}")
PASTA.mkdir(parents=True, exist_ok=True)

print(f"Abrindo navegador...", flush=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    if AUTH_FILE.exists():
        context = browser.new_context(storage_state=str(AUTH_FILE), accept_downloads=True)
    else:
        context = browser.new_context(accept_downloads=True)
        page_login = context.new_page()
        page_login.goto(BASE + "Agenda.aspx")
        print("\n>>> FAÇA LOGIN e depois aperte ENTER aqui...", flush=True)
        input()
        context.storage_state(path=str(AUTH_FILE))
        print(f"    Sessão salva.", flush=True)
        page_login.close()

    page = context.new_page()

    print(f"Indo pra Contas a Pagar...", flush=True)
    page.goto(BASE + "ContaPagar.aspx", wait_until="networkidle", timeout=60_000)
    page.wait_for_timeout(1000)

    # Verificar se está logado (se aparecer ddlStatus)
    if page.locator("#ctl00_cMain_ddlStatus").count() == 0:
        print("❌ Não logado. Faça login manual.", flush=True)
        input(">>> ENTER após logar...")
        context.storage_state(path=str(AUTH_FILE))
        page.goto(BASE + "ContaPagar.aspx", wait_until="networkidle", timeout=60_000)

    print(f"Preenchendo filtros...", flush=True)
    page.select_option("#ctl00_cMain_ddlStatus", "T")
    page.evaluate("""() => {
        document.getElementById('ctl00_cMain_txtDataVencIni').value = '01/01/2026';
        document.getElementById('ctl00_cMain_txtDataVencFim').value = '30/06/2026';
    }""")
    print(f"  ✔ Status=T, Datas=01/01/2026 a 30/06/2026", flush=True)

    print(f"\nClicando Pesquisar e esperando resultado...", flush=True)
    page.click("#ctl00_cMain_btnPesquisar")
    page.wait_for_load_state("networkidle", timeout=90_000)
    page.wait_for_timeout(3000)
    print(f"  ✔ Página resultado carregou. URL: {page.url}", flush=True)

    # Listar TODOS os botões/links visíveis na página de resultado
    print(f"\n=== BOTÕES E LINKS APÓS PESQUISAR ===", flush=True)
    elementos = page.evaluate("""() => {
        const els = [
            ...document.querySelectorAll('input[type=submit]'),
            ...document.querySelectorAll('input[type=button]'),
            ...document.querySelectorAll('button'),
            ...document.querySelectorAll('a[href]'),
            ...document.querySelectorAll('img[onclick]'),
        ];
        return els.map(el => ({
            tag: el.tagName,
            id: el.id,
            name: el.name || '',
            text: (el.value || el.innerText || el.alt || el.title || '').trim().slice(0, 60),
            href: (el.href || '').slice(0, 100),
            onclick: (el.getAttribute('onclick') || '').slice(0, 150),
            visible: el.offsetParent !== null,
        })).filter(e => e.text || e.onclick.includes('Export') || e.onclick.includes('Excel'));
    }""")

    print(f"Total elementos: {len(elementos)}", flush=True)
    for e in elementos:
        marker = "👁 " if e['visible'] else "🚫 "
        print(f"  {marker}<{e['tag']}> id={e['id']!r} text={e['text']!r}", flush=True)
        if e['href']:
            print(f"      href={e['href']!r}", flush=True)
        if e['onclick']:
            print(f"      onclick={e['onclick']!r}", flush=True)

    print(f"\n>>> Verifique visualmente. Deixe navegador aberto.", flush=True)
    input(">>> ENTER pra fechar...")
    browser.close()
