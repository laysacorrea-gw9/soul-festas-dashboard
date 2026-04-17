"""
classify_heuristic.py — classificacao por palavras-chave (sem IA).
Usado como fallback enquanto a conta Anthropic nao tem credito.
Subs futuramente por classify_ai.py (Claude Haiku).
"""
from pathlib import Path
import re
import pandas as pd
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent

# Regras em ordem de prioridade: primeira que bate ganha.
REGRAS = [
    # (palavras-chave, subgrupo, grupo, confianca)
    (["BOLO", "DOCE", "SALGADO", "ALIMENTO", "BEBIDA", "COMIDA"],
     "DESPESAS COM EVENTOS", "DESPESAS OPERACIONAIS E OUTRAS RECEITAS", 0.90),

    (["FILMAKER", "FILMAGEM", "FOTO", "CONVITE", "DJ", "BARMAN", "DECORACAO"],
     "DESPESAS COM EVENTOS", "DESPESAS OPERACIONAIS E OUTRAS RECEITAS", 0.88),

    (["IMPOSTO", "DAEM", "DARF", "INSS", "IPTU", "ISS", "TRIBUTO"],
     "OBRIGAÇÕES / IMPOSTOS", "CUSTOS OPERACIONAIS", 0.95),

    (["ESCALA", "AJUDA DE CUSTO", "ADIANTAMENTO", "SALARIO", "SALÁRIO",
      "FERIAS", "RESCISAO", "RESCISÃO", "EXAME", "DEMISSIONAL", "ADMISSIONAL"],
     "PESSOAL", "CUSTOS OPERACIONAIS", 0.90),

    (["MANUTEN", "REPARO", "ELEVADOR", "CONSERTO"],
     "MANUTENÇÃO CONSERVAÇÃO", "DESPESAS OPERACIONAIS E OUTRAS RECEITAS", 0.88),

    (["CHIP", "INTERNET", "CELULAR", "APARELHO", "TELEFON", "ASSINATURA"],
     "DESPESAS FIXAS", "CUSTOS OPERACIONAIS", 0.85),

    (["COMBUSTIVEL", "COMBUSTÍVEL", "GASOLINA", "UBER", "TAXI", "TRANSPORTE"],
     "DESPESAS GERAIS", "DESPESAS OPERACIONAIS E OUTRAS RECEITAS", 0.80),

    (["PAPEL", "GRAFICA", "GRÁFICA", "PAPELARIA", "TONER", "CARTUCHO",
      "IMPRESS", "ESCRITORIO", "ESCRITÓRIO"],
     "DESPESAS GERAIS", "DESPESAS OPERACIONAIS E OUTRAS RECEITAS", 0.82),

    (["ESTORNO", "EXTORNO", "DEVOLUCAO", "DEVOLUÇÃO", "REEMBOLSO"],
     "OUTROS", "DESPESAS OPERACIONAIS E OUTRAS RECEITAS", 0.70),
]


def classificar_heuristico(servico: str) -> dict:
    s = servico.upper().strip()
    for palavras, sub, grp, conf in REGRAS:
        for p in palavras:
            # boundary so no inicio (pega plural BOLO->BOLOS, mas evita ISS no meio de DEMISSIONAL)
            if re.search(rf"\b{re.escape(p)}", s):
                return {
                    "servico": servico,
                    "subgrupo": sub,
                    "grupo": grp,
                    "confianca": conf,
                    "justificativa": f'Keyword match: "{p}"',
                    "metodo": "heuristica",
                }
    return {
        "servico": servico,
        "subgrupo": "OUTROS",
        "grupo": "DESPESAS OPERACIONAIS E OUTRAS RECEITAS",
        "confianca": 0.30,
        "justificativa": "Sem keyword batendo - fallback OUTROS",
        "metodo": "heuristica-fallback",
    }


def classificar_lote_heuristico(servicos: list[str]) -> pd.DataFrame:
    return pd.DataFrame([classificar_heuristico(s) for s in servicos])


if __name__ == "__main__":
    OUT = ROOT / "ingest" / "data_out"
    nc = pd.read_csv(OUT / "log_nao_classificado.csv")
    pendentes = (
        nc.groupby("Serviço")["Valor Parcela"]
        .agg(qtd="count", valor="sum")
        .sort_values("valor", ascending=False)
        .reset_index()
    )

    resultados = classificar_lote_heuristico(pendentes["Serviço"].tolist())
    df_final = pendentes.merge(resultados, left_on="Serviço", right_on="servico").drop(columns="servico")
    df_final = df_final[["Serviço", "qtd", "valor", "subgrupo", "grupo", "confianca", "justificativa"]]

    out_file = OUT / "classificacoes_heuristica.csv"
    df_final.to_csv(out_file, index=False, encoding="utf-8-sig")

    print(f"=> {len(df_final)} servicos classificados (heuristica)\n")
    print(df_final.to_string(index=False))
    print(f"\n=> Salvo em {out_file}")

    # resumo de confianca
    alta = (df_final["confianca"] >= 0.8).sum()
    media = ((df_final["confianca"] >= 0.6) & (df_final["confianca"] < 0.8)).sum()
    baixa = (df_final["confianca"] < 0.6).sum()
    print(f"\nConfianca: ALTA (>=0.8)={alta} | MEDIA (0.6-0.8)={media} | BAIXA (<0.6)={baixa}")
