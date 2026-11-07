"""Vazios em dados/brutos/onboarding.csv: nulos e textos só com espaços, por coluna.

Só lê o arquivo; nada é gravado. O traço "-" é contado à parte, sem entrar nos vazios.
"""

import hashlib
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "dados" / "brutos" / "onboarding.csv"
LINHAS_DICIONARIO = 63_929

# docs/Vitaliza - Dicionário de dados.pdf, seção 10
OPCIONAL = {
    "objetivo_texto": "sim (texto e tabela)",
    "como_conheceu": "só na tabela; o texto diz que só o objetivo é opcional",
}


def sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.1f}%".replace(".", ",")


def main() -> None:
    hash_antes = sha256(ARQUIVO)

    # texto puro: "NA", "null" etc. continuam como texto, sem virar nulo
    df = pd.read_csv(ARQUIVO, dtype=str, keep_default_na=False)
    total = len(df)

    print("=== 1. linhas e user_id ===")
    print(f"linhas: {fmt(total)} (dicionário: {fmt(LINHAS_DICIONARIO)})")
    ids = df["user_id"].str.strip()
    print(f"user_id únicos: {fmt(ids.nunique())}")
    repetidos = ids[ids.duplicated(keep=False)]
    print(f"user_id repetidos: {fmt(repetidos.nunique())} ids em {fmt(len(repetidos))} linhas")

    linhas = []
    for col in df.columns:
        s = df[col]
        nulos = int((s == "").sum())
        so_espacos = int(((s != "") & (s.str.strip() == "")).sum())
        traco = int((s.str.strip() == "-").sum())
        linhas.append(dict(coluna=col, nulos=nulos, so_espacos=so_espacos,
                           vazios=nulos + so_espacos, traco=traco,
                           opcional=OPCIONAL.get(col, "não")))

    tabela = pd.DataFrame(linhas).sort_values(["vazios", "coluna"], ascending=[False, True])
    print("\n=== 2 e 3. vazios por coluna (mais vazia primeiro) ===")
    print(f"{'coluna':<17}{'nulos':>8}{'só espaços':>12}{'total':>8}{'%':>7}{'traço -':>9}  opcional no dicionário")
    for r in tabela.itertuples():
        print(f"{r.coluna:<17}{fmt(r.nulos):>8}{fmt(r.so_espacos):>12}{fmt(r.vazios):>8}"
              f"{pct(r.vazios, total):>7}{fmt(r.traco):>9}  {r.opcional}")

    # exemplos dos tipos de espaço encontrados, para conferência
    espacos = pd.concat([df[c][(df[c] != "") & (df[c].str.strip() == "")] for c in df.columns])
    if len(espacos):
        print("\nformas de 'só espaços' encontradas:",
              ", ".join(f"{repr(v)} ({fmt(n)})" for v, n in espacos.value_counts().head(5).items()))

    print(f"\nonboarding.csv {'inalterado' if sha256(ARQUIVO) == hash_antes else 'ALTERADO'}")


if __name__ == "__main__":
    main()
