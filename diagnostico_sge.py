"""
Diagnóstico SGE — inspeciona as páginas dos relatórios e lista os selectores REAIS.
Rodar UMA VEZ pra descobrir os IDs corretos dos <select> e <input> em cada página.
Depois usar os resultados pra corrigir o baixar_relatorios_sge.py.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Força UTF-8 no stdout do Windows
sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://sistema.sge.com.br/SGE/Forms/"
AUTH_FILE = Path("sge_auth.json")

PAGINAS = [
    ("ContaPagar.aspx", "Contas a Pagar"),
    ("ContasAReceber.aspx", "Contas a Receber"),
    ("Reports/RelAgenda.aspx", "Agenda"),
    ("Reports/RelBalancoDoContrato.aspx", "Balanço por Projeto"),
    ("Reports/RelCustosDoProjeto.aspx", "Custo do Projeto"),
    ("Reports/RelClientesInadimplentes.aspx", "Inadimplentes"),
]

def inspecionar(page, url_relativo, nome):
    url_completa = BASE + url_relativo
    print("\n" + "=" * 70)
    print(f"PÁGINA: {nome}")
    print(f"URL: {url_completa}")
    print("=" * 70)
    try:
        page.goto(url_completa, wait_until="networkidle", timeout=60000)
    except Exception as e:
        print(f"❌ Falha ao carregar página: {e}")
        return

    # Listar SELECTS
    print("\n--- SELECTS na página ---")
    try:
        selects = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('select')).map(s => {
                const label = s.labels && s.labels[0] ? s.labels[0].innerText.trim() : '';
                const options = Array.from(s.options).slice(0, 6).map(o => `[${o.value}]${o.text.trim()}`).join(' | ');
                return { id: s.id, name: s.name, label, options };
            });
        }""")
        if not selects:
            print("  (nenhum select encontrado)")
        for s in selects:
            print(f"  ▪ id={s['id']!r}")
            print(f"    name={s['name']!r}")
            print(f"    label={s['label']!r}")
            print(f"    options={s['options']}")
    except Exception as e:
        print(f"❌ Erro listando selects: {e}")

    # Listar INPUTS de data (com placeholder ou type=date/text)
    print("\n--- INPUTS de data ---")
    try:
        inputs = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('input')).filter(i => {
                const ph = (i.placeholder || '').toLowerCase();
                return ph.includes('de') || ph.includes('até') || ph.includes('ate') || i.type === 'date' || (i.className || '').includes('date');
            }).map(i => ({
                id: i.id, name: i.name, placeholder: i.placeholder, type: i.type, cls: i.className
            }));
        }""")
        if not inputs:
            print("  (nenhum input de data encontrado)")
        for i, inp in enumerate(inputs):
            print(f"  [{i}] id={inp['id']!r} name={inp['name']!r} placeholder={inp['placeholder']!r}")
    except Exception as e:
        print(f"❌ Erro listando inputs: {e}")

    # Listar BUTTONS
    print("\n--- BOTÕES visíveis ---")
    try:
        buttons = page.evaluate("""() => {
            const els = [
                ...document.querySelectorAll('button'),
                ...document.querySelectorAll('input[type=submit]'),
                ...document.querySelectorAll('input[type=button]'),
                ...document.querySelectorAll('a.btn'),
            ];
            return els.map(b => ({
                tag: b.tagName,
                id: b.id,
                text: (b.innerText || b.value || '').trim().slice(0, 60),
                onclick: (b.getAttribute('onclick') || '').slice(0, 100),
            })).filter(b => b.text);
        }""")
        for b in buttons[:15]:
            print(f"  ▪ <{b['tag']}> id={b['id']!r} text={b['text']!r}")
            if b['onclick']:
                print(f"    onclick={b['onclick']!r}")
    except Exception as e:
        print(f"❌ Erro listando botões: {e}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        if AUTH_FILE.exists():
            context = browser.new_context(storage_state=str(AUTH_FILE), accept_downloads=True)
            print(f"✔ Sessão carregada de {AUTH_FILE}")
        else:
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.goto(BASE + "Agenda.aspx")
            print("\n>>> FAÇA O LOGIN no navegador que abriu.")
            input(">>> Depois de logar, aperte ENTER aqui...")
            context.storage_state(path=str(AUTH_FILE))

        page = context.new_page() if AUTH_FILE.exists() else context.pages[0]

        for url, nome in PAGINAS:
            inspecionar(page, url, nome)

        print("\n\n✅ Diagnóstico concluído. Feche o navegador quando quiser.")
        input(">>> ENTER pra fechar o navegador...")
        browser.close()


if __name__ == "__main__":
    main()
