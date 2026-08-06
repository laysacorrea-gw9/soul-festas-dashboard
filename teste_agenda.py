"""
Teste isolado: SÓ baixar Agenda Resumida.
Se funcionar, sabemos que a base tá ok e podemos expandir.
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

print(f"[1/5] Abrindo Playwright...", flush=True)

with sync_playwright() as p:
    print(f"[2/5] Lançando Chromium (visível)...", flush=True)
    browser = p.chromium.launch(headless=False)

    print(f"[3/5] Criando contexto com sessão de {AUTH_FILE}...", flush=True)
    context = browser.new_context(storage_state=str(AUTH_FILE), accept_downloads=True)
    page = context.new_page()

    print(f"[4/5] Navegando para Agenda...", flush=True)
    page.goto(BASE + "Reports/RelAgenda.aspx", timeout=60_000)
    print(f"       URL atual: {page.url}", flush=True)
    page.wait_for_load_state("networkidle", timeout=60_000)
    print(f"       Página carregada.", flush=True)

    print(f"[5/5] Selecionando tipo 'Resumido (Planilha)' (RP)...", flush=True)
    page.select_option("#ctl00_cMain_ddlTipoRelatorio", "RP")
    print(f"       ✔ Tipo selecionado", flush=True)

    print(f"       Expandindo accordion 'PERÍODO DE REALIZAÇÃO DO EVENTO'...", flush=True)
    # Tentar 3 estratégias
    for tentativa in [
        lambda: page.click("text=PERÍODO DE REALIZAÇÃO DO EVENTO", timeout=5000),
        lambda: page.click("text=/período.*evento/i", timeout=5000),
        lambda: page.locator("legend, .accordion-header, .panel-heading").filter(has_text="período").first.click(timeout=5000),
    ]:
        try:
            tentativa()
            print(f"       ✔ Accordion clicado", flush=True)
            break
        except Exception as e:
            print(f"       (tentativa falhou: {type(e).__name__})", flush=True)
    page.wait_for_timeout(1000)

    print(f"       Preenchendo datas via JS (garante que funciona mesmo se oculto)...", flush=True)
    page.evaluate("""() => {
        const setar = (id, valor) => {
            const el = document.getElementById(id);
            if (el) {
                el.value = valor;
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
            }
        };
        setar('ctl00_cMain_periodoEvento_txtDataIni', '01/01/2025');
        setar('ctl00_cMain_periodoEvento_txtDataFim', '31/12/2027');
    }""")
    print(f"       ✔ Datas preenchidas", flush=True)

    destino = PASTA / "AgendaResumida.xlsx"
    print(f"       Clicando 'Gerar Relatório' e aguardando download...", flush=True)
    print(f"       (destino: {destino})", flush=True)

    try:
        with page.expect_download(timeout=180_000) as dl_info:
            page.click("#ctl00_cMain_btnGerarRelatorio")
            print(f"       ✔ Botão clicado. Aguardando download...", flush=True)
        download = dl_info.value
        print(f"       ✔ Download recebido: {download.suggested_filename}", flush=True)
        download.save_as(str(destino))
        tamanho = destino.stat().st_size
        print(f"       ✅ SALVO: {destino.name} ({tamanho:,} bytes)", flush=True)
    except Exception as e:
        print(f"       ❌ ERRO: {type(e).__name__}: {e}", flush=True)

    print(f"\nFechando navegador...", flush=True)
    browser.close()
    print(f"OK - teste concluído.", flush=True)
