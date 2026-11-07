"""Análise 4 · Consistência da coluna `tipo` em dados/brutos/atividades.parquet (Colaborador 2).

A mesma categoria escrita de mais de um jeito (corrida/run, caminhada/walk…).
Propõe o mapa de padronização SEM aplicar: só lê o arquivo (hash SHA-256
conferido antes e depois).

Roteiro: docs/analises_por_colaborador/colaborador_2.md, análise 4.
"""

import hashlib
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "dados" / "brutos" / "atividades.parquet"

# Proposta (não aplicada): inglês -> português, mantendo o português como canônico
MAPA = {"run": "corrida", "walk": "caminhada", "ride": "pedal", "strength": "forca"}


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def fmt(n) -> str:
    return f"{n:,}".replace(",", ".")


def main() -> None:
    hash_antes = sha256(ARQUIVO)
    df = pd.read_parquet(ARQUIVO, columns=["tipo", "origem"])
    total = len(df)
    print(f"treinos lidos: {fmt(total)}")

    print("\n=== 1. valores de tipo ===")
    vc = df["tipo"].value_counts(dropna=False)
    print(vc.to_string())
    print(f"valores distintos: {vc.size}")

    print("\n=== 2. tipo × origem ===")
    tab = pd.crosstab(df["tipo"], df["origem"], margins=True)
    print(tab.to_string())

    print("\n=== 3. mapa de padronização proposto (NÃO aplicado) ===")
    em_ingles = df["tipo"].isin(MAPA).sum()
    for ing, pt in MAPA.items():
        n_ing, n_pt = int(vc.get(ing, 0)), int(vc.get(pt, 0))
        print(f"{ing:<9} -> {pt:<10} afeta {fmt(n_ing):>8} linhas (junta com {fmt(n_pt)} em pt = {fmt(n_ing + n_pt)})")
    print(f"\ntotal em inglês: {fmt(em_ingles)} ({100 * em_ingles / total:.1f}%)")
    origem_ingles = df.loc[df["tipo"].isin(MAPA), "origem"].value_counts()
    print("origem dos nomes em inglês:")
    print(origem_ingles.to_string())

    print("\n=== 4. efeito por troca e categorias finais ===")
    depois = df["tipo"].map(lambda t: MAPA.get(t, t)).value_counts()
    print(f"categorias depois do mapa: {depois.size}")
    print(depois.to_string())

    estado = "inalterado" if sha256(ARQUIVO) == hash_antes else "ALTERADO"
    print(f"\natividades.parquet {estado} ({hash_antes[:16]}…)")


if __name__ == "__main__":
    main()
