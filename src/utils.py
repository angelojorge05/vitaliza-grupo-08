"""Funções comuns às análises do colaborador 1 (análises 1, 7 e 11).

Só leitura de dados/brutos/. Nada aqui altera arquivo bruto.
"""

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos"
PROCESSADOS = RAIZ / "dados" / "processados"
SAIDAS = RAIZ / "saidas"

CORTE = pd.Timestamp("2026-09-30 23:59:59")  # horário de Brasília
FUSO = "America/Sao_Paulo"
DOMINIO_TESTE = "@vitaliza.com.br"


def mostrar(rotulo: str, df: pd.DataFrame, antes: int | None = None) -> pd.DataFrame:
    """Imprime a contagem de linhas depois de um filtro ou junção (e quantas saíram)."""
    milhar = lambda n, sinal="": f"{n:{sinal},}".replace(",", ".")
    msg = f"[linhas] {rotulo}: {milhar(len(df))}"
    if antes is not None:
        msg += f" (antes {milhar(antes)}, diferença {milhar(len(df) - antes, '+')})"
    print(msg)
    return df


def contas_de_teste() -> set[str]:
    """user_id das contas de teste (e-mail @vitaliza.com.br, sem diferenciar maiúsculas)."""
    u = pd.read_csv(BRUTOS / "usuarios.csv", usecols=["user_id", "email"], dtype=str)
    teste = u["email"].str.strip().str.lower().str.endswith(DOMINIO_TESTE, na=False)
    return set(u.loc[teste, "user_id"])


def para_brasilia(s: pd.Series) -> pd.Series:
    """Texto de data/hora -> horário de Brasília sem fuso.

    Valores com Z (ou deslocamento) são UTC e convertidos; valores sem fuso já estão em
    Brasília (eventos do site, segundo o contexto do case). O que não casa vira NaT.
    """
    s = s.astype("string").str.strip()
    com_fuso = s.str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", regex=True, na=False)
    saida = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    if com_fuso.any():
        utc = pd.to_datetime(s[com_fuso], format="ISO8601", utc=True, errors="coerce")
        saida[com_fuso] = utc.dt.tz_convert(FUSO).dt.tz_localize(None).astype("datetime64[ns]")
    sem = ~com_fuso & s.notna()
    if sem.any():
        saida[sem] = pd.to_datetime(s[sem], format="ISO8601", errors="coerce").astype("datetime64[ns]")
    return saida
