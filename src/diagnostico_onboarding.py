"""Passo 1 · diagnóstico do onboarding antes de padronizar (só leitura).

Lê dados/brutos/onboarding.csv e usuarios.csv; grava apenas saidas/diagnostico_onboarding.md.
Rodar da raiz:  python -I src/diagnostico_onboarding.py
"""

import hashlib
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import BRUTOS, CORTE, SAIDAS, mostrar  # noqa: E402


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    h0 = sha(BRUTOS / "onboarding.csv"), sha(BRUTOS / "usuarios.csv")
    ob = pd.read_csv(BRUTOS / "onboarding.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    us = pd.read_csv(BRUTOS / "usuarios.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    mostrar("onboarding.csv", ob)
    mostrar("usuarios.csv", us)
    out = ["# Diagnóstico do onboarding (Passo 1, só leitura)", ""]

    # 1. formas de dias_por_semana
    d = ob["dias_por_semana"].value_counts()
    out += ["## `dias_por_semana`: formas encontradas", "", f"{len(d)} formas distintas (incluindo o vazio).", "",
            "| Forma | Linhas |", "|---|---:|"]
    for k, v in d.items():
        out.append(f"| `{k if k else '(vazio)'}` | {fmt(int(v))} |")
    print(f"dias_por_semana: {len(d)} formas")

    # 2. espaços nas pontas e caixa
    out += ["", "## Espaços nas pontas e caixa", "", "| Coluna | Com espaço nas pontas | Valores que diferem só pela caixa |", "|---|---:|---:|"]
    for col in ["nivel", "dias_por_semana", "objetivo_texto", "como_conheceu"]:
        s = ob[col]
        esp = int(((s != s.str.strip())).sum())
        caixa = int(s.str.strip().nunique() - s.str.strip().str.lower().nunique())
        out.append(f"| `{col}` | {fmt(esp)} | {caixa} |")
        print(f"{col}: espaço nas pontas {esp}, variações só de caixa {caixa}")

    # 3. respondido_em
    r = ob["respondido_em"]
    padrao = r.str.replace(r"\d", "9", regex=True)
    out += ["", "## `respondido_em`: formatos", "", "| Formato (9 = dígito) | Linhas |", "|---|---:|"]
    for k, v in padrao.value_counts().items():
        out.append(f"| `{k}` | {fmt(int(v))} |")
    print("formatos de respondido_em:", padrao.value_counts().to_dict())
    dt = pd.to_datetime(r, format="%Y-%m-%d", errors="coerce")
    ilegiveis = int(dt.isna().sum())
    apos = int((dt > CORTE).sum())
    out += ["", f"- Datas que não leem como `AAAA-MM-DD`: **{fmt(ilegiveis)}**.",
            f"- Datas depois do corte (30/09/2026): **{fmt(apos)}**.",
            f"- Intervalo: {dt.min().date()} a {dt.max().date()}."]
    print(f"respondido_em ilegíveis {ilegiveis}, após corte {apos}, de {dt.min().date()} a {dt.max().date()}")

    # 4. cobertura e duplicatas
    ids_ob, ids_us = set(ob["user_id"]), set(us["user_id"])
    dup_ob = int(ob["user_id"].duplicated().sum())
    dup_us = int(us["user_id"].duplicated().sum())
    sem_ob = len(ids_us - ids_ob)
    orfaos = len(ids_ob - ids_us)
    out += ["", "## Cobertura e duplicatas", "",
            f"- `usuarios.csv`: {fmt(len(us))} linhas, {fmt(len(ids_us))} `user_id` únicos, **{fmt(dup_us)} duplicados**.",
            f"- `onboarding.csv`: {fmt(len(ob))} linhas, {fmt(len(ids_ob))} `user_id` únicos, **{fmt(dup_ob)} duplicados**.",
            f"- Contas de `usuarios.csv` sem linha no onboarding: **{fmt(sem_ob)}**.",
            f"- `user_id` do onboarding que não existem em `usuarios.csv`: **{fmt(orfaos)}**."]
    print(f"duplicados us {dup_us}, ob {dup_ob}; contas sem onboarding {sem_ob}; órfãos {orfaos}")

    assert (sha(BRUTOS / "onboarding.csv"), sha(BRUTOS / "usuarios.csv")) == h0
    out += ["", "SHA-256 de `onboarding.csv` e `usuarios.csv` igual antes e depois: o bruto não foi tocado.", ""]
    SAIDAS.mkdir(exist_ok=True)
    (SAIDAS / "diagnostico_onboarding.md").write_text("\n".join(out), encoding="utf-8")
    print("gravado saidas/diagnostico_onboarding.md")


if __name__ == "__main__":
    main()
