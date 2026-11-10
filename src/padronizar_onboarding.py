"""Passo 2 · padronização do onboarding.

Lê dados/brutos/onboarding.csv (só leitura) e grava dados/processados/onboarding_padronizado.csv:
todas as colunas originais, sem alteração, mais:
  - dias_por_semana_num   : 1 a 7 (inteiro); vazio e "todos" ficam sem número
  - dias_por_semana_todos : True quando a resposta foi "todos" (sem interpretar como 7)
Decisões do usuário (09/11/2026): "todos" sem número; colunas originais mantidas.
`nivel`, `respondido_em` e os textos livres não precisam de mudança (ver diagnostico_onboarding.md).

Rodar da raiz:  python -I src/padronizar_onboarding.py
"""

import hashlib
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import BRUTOS, PROCESSADOS, mostrar  # noqa: E402

PADRAO = r"^([1-7])(?:\s*(?:x|vezes))?$"


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def main() -> None:
    arq = BRUTOS / "onboarding.csv"
    h0 = hashlib.sha256(arq.read_bytes()).hexdigest()
    df = pd.read_csv(arq, dtype=str, keep_default_na=False, encoding="utf-8")
    n = len(mostrar("onboarding.csv", df))

    s = df["dias_por_semana"].str.strip().str.lower()
    extraido = s.str.extract(PADRAO, expand=False)
    df["dias_por_semana_num"] = pd.to_numeric(extraido, errors="coerce").astype("Int64")
    df["dias_por_semana_todos"] = s.eq("todos")

    vazio = s.eq("")
    n_num = int(df["dias_por_semana_num"].notna().sum())
    n_todos = int(df["dias_por_semana_todos"].sum())
    n_vazio = int(vazio.sum())
    nao_lidos = df.loc[~vazio & ~df["dias_por_semana_todos"] & df["dias_por_semana_num"].isna(), "dias_por_semana"]
    print(f"com número (1 a 7): {fmt(n_num)} | 'todos': {fmt(n_todos)} | vazios: {fmt(n_vazio)} | não lidos: {len(nao_lidos)}")
    print(f"soma: {fmt(n_num + n_todos + n_vazio)} (esperado {fmt(n)})")
    assert len(nao_lidos) == 0, f"formas não previstas: {nao_lidos.unique().tolist()}"
    assert n_num + n_todos + n_vazio == n

    # o número extraído reproduz o texto original
    amostra = df[df["dias_por_semana_num"].notna()].drop_duplicates("dias_por_semana")[["dias_por_semana", "dias_por_semana_num"]]
    print("formas -> número:")
    print(amostra.sort_values("dias_por_semana_num").to_string(index=False))

    print("distribuição do número:", df["dias_por_semana_num"].value_counts().sort_index().to_dict())

    assert len(df) == n and df["user_id"].is_unique, "linhas ou user_id duplicados"
    PROCESSADOS.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSADOS / "onboarding_padronizado.csv", index=False, encoding="utf-8")
    mostrar("onboarding_padronizado.csv gravado", df, n)
    assert hashlib.sha256(arq.read_bytes()).hexdigest() == h0, "o arquivo bruto mudou!"
    print("hash do bruto igual antes/depois: True")


if __name__ == "__main__":
    main()
