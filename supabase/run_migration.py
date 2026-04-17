"""Executa migrations via Supabase Management API (HTTPS, evita problema IPv6)."""
from pathlib import Path
import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

PROJECT_REF = os.getenv("SUPABASE_PROJECT_ID")
PAT = os.getenv("SUPABASE_PAT")
API = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query"
HEADERS = {"Authorization": f"Bearer {PAT}", "Content-Type": "application/json"}


def run_sql(sql: str) -> dict:
    r = requests.post(API, json={"query": sql}, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()


def main():
    mig_dir = Path(__file__).parent / "migrations"
    arquivos = sorted(mig_dir.glob("*.sql"))

    for f in arquivos:
        print(f"=> Executando {f.name}...")
        sql = f.read_text(encoding="utf-8")
        try:
            run_sql(sql)
            print(f"   OK")
        except requests.HTTPError as e:
            print(f"   ERRO HTTP {e.response.status_code}: {e.response.text[:500]}")
            raise

    # valida
    res = run_sql("select table_name from information_schema.tables where table_schema='soul' order by 1")
    tables = [row["table_name"] for row in res]
    print(f"\n=> Tabelas criadas em soul ({len(tables)}):")
    for t in tables:
        print(f"   - soul.{t}")


if __name__ == "__main__":
    main()