"""Gera de_para_natureza_servico.csv: cada Serviço -> EVENTO ou CASA.

Classificacao por NATUREZA do servico (nao pela presenca de projeto).
Tudo que nao for explicitamente EVENTO vai pra CASA (linha conservadora da Laysa).
Decisoes ambiguas confirmadas pela Laysa em 16/06/2026:
  - Bombeiro, Mao de obra, Diesel, Letreiro, ECAD, Lavanderia, Pipa d'agua, Gas -> CASA
  - Diaria e Seguranca (do dia do evento), Comissao de vendas -> EVENTO
"""
from pathlib import Path
import sys
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent

EVENTO = {
    "ALIMENTOS", "STAFF DE EVENTOS", "DECORAÇÃO", "BEBIDAS", "FLORES E ARRANJOS",
    "LEDS", "DJ", "BOLOS E DOCES", "CERIMONIAL", "BOLO FAKE",
    "TOALHAS E GUARDANAPOS", "SALGADOS", "DOCES FINOS", "DESCARTÁVEIS", "GERADOR",
    "DIESEL", "ESTORNO RESCISÃO",
    "MOBILIÁRIO", "VJ", "VALET", "VELAS", "CABINE DE FOTOS", "EXTRAS DE DECORAÇÃO",
    "LETICIA BALÕES", "CHOPP", "FOGOS INDOOR", "ILUMINAÇÃO", "BOLO ANIVERSARIANTE",
    "OPEN BAR", "GERENTE DE EVENTO", "VALET E SEGURANÇA", "ESCALA", "PÓS DE EVENTO",
    "RING LIGHT", "DVD COM FOTOS", "BARMAN", "FILMAKER", "LINK DE FOTOS TRATADO",
    "DIÁRIA DE EVENTO", "COPO ECO 450ML", "CHOCOLATES FINOS", "SUPORTE DECORACAO",
    "CONVITE PARA CONVIDADOS", "SUSHIMAN", "ALIMENTAÇÃO STAFF", "FORMINHAS",
    "BUFFET OURO", "PISTA DE DANÇA", "CONVITES PARA EVENTOS", "ESPAÇO KIDS",
    "RIDER BANDA", "GELO", "GELO E ÁGUA", "BOLOS E DOCES VEGANOS", "ACRILICO",
    "CANUDO", "MICROFONE DE LAPELA", "MANUTENÇÃO DO SOM", "DIÁRIA", "SEGURANÇA",
}


def natureza(servico: str) -> str:
    return "EVENTO" if str(servico).strip().upper() in EVENTO else "CASA"


def main():
    pg = pd.read_csv(ROOT / "data_out" / "contas_pagar_final.csv", low_memory=False)
    servicos = sorted(pg["Serviço"].dropna().astype(str).str.strip().unique())
    rows = [{"servico": s, "natureza": natureza(s)} for s in servicos]
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "de_para_natureza_servico.csv", index=False, encoding="utf-8")

    ev = df[df["natureza"] == "EVENTO"]
    print(f"Total servicos: {len(df)} | EVENTO: {len(ev)} | CASA: {len(df) - len(ev)}")
    print("\nServicos classificados como EVENTO:")
    for s in ev["servico"]:
        print(f"  - {s}")


if __name__ == "__main__":
    main()