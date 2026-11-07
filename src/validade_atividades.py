"""Análise 3 · Validade de dados/brutos/atividades.parquet (Colaborador 2).

Distâncias e durações que não podem ser reais, sem confundir com o que só
está vazio. Só lê o arquivo; nada é gravado em dados/brutos/ (hash SHA-256
conferido antes e depois).

Roteiro: docs/analises_por_colaborador/colaborador_2.md, análise 3.
"""

import hashlib
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "dados" / "brutos" / "atividades.parquet"
LINHAS_DICIONARIO = 1_254_475
LIMIAR_KM = 200


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def fmt(n) -> str:
    return f"{n:,.0f}".replace(",", ".") if float(n).is_integer() else f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main() -> None:
    hash_antes = sha256(ARQUIVO)
    df = pd.read_parquet(ARQUIVO, columns=None)

    print("=== 1. contagens ===")
    total = len(df)
    com_dist = df["distancia_km"].notna().sum()
    print(f"treinos: {fmt(total)} (dicionário: {fmt(LINHAS_DICIONARIO)})")
    print(f"com distancia_km preenchida: {fmt(com_dist)} "
          f"({100 * com_dist / total:.1f}%) · sem distância: {fmt(total - com_dist)} (sem GPS, não é erro)")

    print("\n=== 2. mínimo, mediana e máximo ===")
    for col in ("distancia_km", "duracao_min"):
        s = df[col].dropna()
        print(f"{col:<14} n={fmt(len(s))}  mín={s.min():g}  mediana={s.median():g}  máx={s.max():,.2f}")

    print(f"\n=== 3. valores impossíveis ===")
    acima = df[df["distancia_km"] > LIMIAR_KM]
    dur_zero = df[df["duracao_min"] == 0]
    dur_neg = df[df["duracao_min"] < 0]
    print(f"distancia_km > {LIMIAR_KM}: {fmt(len(acima))} treinos")
    print(f"duracao_min = 0: {fmt(len(dur_zero))} treinos · duracao_min < 0: {fmt(len(dur_neg))}")
    print("\npor tipo (distância > 200 km):")
    print(acima["tipo"].value_counts().to_string())
    print("\npor origem (distância > 200 km):")
    print(acima["origem"].value_counts().to_string())

    print("\n=== 4. os cinco treinos mais longos (todas as colunas) ===")
    top5 = df.nlargest(5, "distancia_km")
    with pd.option_context("display.width", 200, "display.max_columns", None):
        print(top5.to_string(index=False))

    estado = "inalterado" if sha256(ARQUIVO) == hash_antes else "ALTERADO"
    print(f"\natividades.parquet {estado} ({hash_antes[:16]}…)")


if __name__ == "__main__":
    main()
