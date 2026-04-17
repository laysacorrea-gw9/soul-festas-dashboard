"""
classify_ai.py — classificacao de Servico SGE -> Subgrupo/Grupo via Claude Haiku 4.5.

Usa prompt caching pra que os 134 exemplos do de-para virem cache (1h TTL),
reduzindo custo e latencia em chamadas subsequentes.

Uso:
    from classify_ai import classificar_lote
    resultado = classificar_lote(["BOLOS E DOCES", "ESCALA", ...])
"""
from pathlib import Path
import json
import os
import pandas as pd
from dotenv import load_dotenv
from anthropic import Anthropic

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / ".env")

_client = Anthropic()
MODEL = "claude-haiku-4-5-20251001"


def _carregar_exemplos() -> list[dict]:
    from transform import load_de_para_subgrupo
    df = load_de_para_subgrupo()
    return df.to_dict(orient="records")


def _montar_system_prompt(exemplos: list[dict]) -> list[dict]:
    """System prompt com exemplos cacheados."""
    linhas = "\n".join(
        f"- {e['servico']} | {e['subgrupo']} | {e['grupo']}"
        for e in exemplos
    )
    grupos_unicos = sorted({e["grupo"] for e in exemplos})
    subgrupos_unicos = sorted({e["subgrupo"] for e in exemplos})

    texto = f"""Voce classifica servicos de uma casa de festas/eventos (Soul Festas) em Grupo e Subgrupo contabeis.

REGRAS:
1. Escolha APENAS entre os Grupos existentes: {grupos_unicos}
2. Escolha APENAS entre os Subgrupos existentes: {subgrupos_unicos}
3. Respeite a relacao Subgrupo -> Grupo dos exemplos abaixo
4. Responda SEMPRE em JSON valido com: subgrupo, grupo, confianca (0-1), justificativa (1 frase curta)
5. Se nao tiver certeza, use confianca baixa (<0.6) e escolha o mais provavel

EXEMPLOS DE CLASSIFICACAO (SERVICO | SUBGRUPO | GRUPO):
{linhas}
"""
    return [{
        "type": "text",
        "text": texto,
        "cache_control": {"type": "ephemeral"},
    }]


def classificar_um(servico: str, exemplos: list[dict] | None = None) -> dict:
    if exemplos is None:
        exemplos = _carregar_exemplos()
    system = _montar_system_prompt(exemplos)

    resp = _client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=system,
        messages=[{
            "role": "user",
            "content": f'Classifique: "{servico}"\n\nResponda apenas o JSON.',
        }],
    )
    txt = resp.content[0].text.strip()
    if txt.startswith("```"):
        txt = txt.split("```")[1]
        if txt.startswith("json"):
            txt = txt[4:]
        txt = txt.strip()
    out = json.loads(txt)
    out["servico"] = servico
    out["cache_hits"] = getattr(resp.usage, "cache_read_input_tokens", 0)
    return out


def classificar_lote(servicos: list[str]) -> pd.DataFrame:
    exemplos = _carregar_exemplos()
    resultados = []
    for i, s in enumerate(servicos, 1):
        print(f"  [{i}/{len(servicos)}] {s}...", end=" ", flush=True)
        try:
            r = classificar_um(s, exemplos)
            resultados.append(r)
            print(f"-> {r['subgrupo']} / conf={r['confianca']:.2f}")
        except Exception as e:
            print(f"ERRO: {e}")
            resultados.append({"servico": s, "erro": str(e)})
    return pd.DataFrame(resultados)


if __name__ == "__main__":
    # Teste com os 17 pendentes
    OUT = ROOT / "ingest" / "data_out"
    nc = pd.read_csv(OUT / "log_nao_classificado.csv")
    servicos_pendentes = (
        nc.groupby("Serviço")["Valor Parcela"].sum()
        .sort_values(ascending=False)
        .index.tolist()
    )
    print(f"=> Classificando {len(servicos_pendentes)} servicos pendentes via Claude Haiku...\n")
    df = classificar_lote(servicos_pendentes)
    out_file = OUT / "classificacoes_ia.csv"
    df.to_csv(out_file, index=False, encoding="utf-8-sig")
    print(f"\n=> Salvo em {out_file}")
    print("\nResumo:")
    if "confianca" in df.columns:
        print(df[["servico", "subgrupo", "grupo", "confianca", "justificativa"]].to_string(index=False))
