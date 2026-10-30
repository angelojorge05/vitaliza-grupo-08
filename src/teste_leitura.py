"""Teste de leitura: um CSV e o parquet de dados/brutos/.

Só lê os arquivos. Confere a contagem de linhas contra o dicionário de dados
e garante, por hash SHA-256, que nada em dados/brutos/ foi alterado.
"""

import hashlib
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos"

# linhas esperadas segundo docs/Vitaliza - Dicionário de dados.pdf
ARQUIVOS = {
    "usuarios.csv": 64_948,
    "atividades.parquet": 1_254_475,
}


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def ler(caminho: Path) -> pd.DataFrame:
    if caminho.suffix == ".parquet":
        return pd.read_parquet(caminho)
    # dtype=str: lê como veio, sem o pandas adivinhar tipos
    return pd.read_csv(caminho, dtype=str)


def mascarar_email(df: pd.DataFrame) -> pd.DataFrame:
    if "email" in df.columns:
        df = df.copy()
        df["email"] = df["email"].str.replace(r"^[^@]+", "***", regex=True)
    return df


def main() -> None:
    hashes_antes = {nome: sha256(BRUTOS / nome) for nome in ARQUIVOS}
    tudo_ok = True

    for nome, esperado in ARQUIVOS.items():
        df = ler(BRUTOS / nome)
        bate = len(df) == esperado
        tudo_ok &= bate

        print(f"\n=== {nome} ===")
        print(f"linhas: {len(df):,} | esperado: {esperado:,} | {'OK' if bate else 'DIVERGE'}")
        print(f"colunas ({df.shape[1]}): {list(df.columns)}")
        print("\ntipos:")
        print(df.dtypes.to_string())
        print("\nexemplo (3 linhas):")
        with pd.option_context("display.width", 200, "display.max_columns", None):
            print(mascarar_email(df.head(3)).to_string())

    print("\n=== integridade de dados/brutos/ ===")
    for nome, antes in hashes_antes.items():
        depois = sha256(BRUTOS / nome)
        igual = antes == depois
        tudo_ok &= igual
        print(f"{nome}: {'inalterado' if igual else 'ALTERADO'} ({depois[:16]}...)")

    print(f"\nresultado: {'OK' if tudo_ok else 'FALHOU'}")


if __name__ == "__main__":
    main()
