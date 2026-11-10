"""Passo 3 · completude do onboarding: marcar lacunas, sem preencher nenhum vazio.

Lê dados/processados/onboarding_padronizado.csv (saída do passo 2) e o regrava com 4 marcas:
  nivel_nao_informado, dias_por_semana_nao_informado, objetivo_sem_resposta, como_conheceu_sem_resposta
Os valores originais continuam como estão. Grava saidas/completude_marcas_onboarding.md.

Rodar da raiz:  python -I src/marcas_completude_onboarding.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import PROCESSADOS, SAIDAS, mostrar  # noqa: E402

COLUNAS_ORIG = ["onboarding_id", "user_id", "respondido_em", "objetivo_texto", "como_conheceu", "nivel", "dias_por_semana"]
OBRIGATORIAS = ["onboarding_id", "user_id", "respondido_em", "nivel", "dias_por_semana"]


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.2f}%".replace(".", ",")


def medidas(vz: pd.DataFrame) -> dict:
    n = len(vz)
    cel = vz.size
    obr = vz[OBRIGATORIAS]
    return dict(
        celulas=cel, vazias=int(vz.sum().sum()), preenchidas=1 - vz.sum().sum() / cel,
        obr_cel=obr.size, obr_vazias=int(obr.sum().sum()), obr_pre=1 - obr.sum().sum() / obr.size,
        lin_comp=int((~vz.any(axis=1)).sum()), lin_comp_obr=int((~obr.any(axis=1)).sum()), n=n,
    )


def main() -> None:
    df = pd.read_csv(PROCESSADOS / "onboarding_padronizado.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    n = len(mostrar("onboarding_padronizado.csv", df))
    assert df["user_id"].is_unique

    orig = df[COLUNAS_ORIG]
    vazio = orig.apply(lambda s: s.str.strip() == "")
    traco = orig.apply(lambda s: s.str.strip() == "-")
    antes = medidas(vazio)

    df["nivel_nao_informado"] = vazio["nivel"]
    df["dias_por_semana_nao_informado"] = vazio["dias_por_semana"]
    df["objetivo_sem_resposta"] = vazio["objetivo_texto"] | traco["objetivo_texto"]
    df["como_conheceu_sem_resposta"] = vazio["como_conheceu"] | traco["como_conheceu"]

    marcas = {c: int(df[c].sum()) for c in ["nivel_nao_informado", "dias_por_semana_nao_informado",
                                            "objetivo_sem_resposta", "como_conheceu_sem_resposta"]}
    esperado = {"nivel_nao_informado": 4513, "dias_por_semana_nao_informado": 6368,
                "objetivo_sem_resposta": 6789, "como_conheceu_sem_resposta": 5776}
    for k, v in marcas.items():
        print(f"{k}: {fmt(v)} (esperado {fmt(esperado[k])}) -> {'ok' if v == esperado[k] else 'DIVERGE'}")
        assert v == esperado[k]

    # nenhum vazio foi preenchido: a parte original é idêntica antes e depois
    assert df[COLUNAS_ORIG].equals(orig)
    assert len(df) == n and df["user_id"].is_unique

    # uso depois da padronização
    com_num = int((df["dias_por_semana_num"] != "").sum())
    todos = int((df["dias_por_semana_todos"] == "True").sum())
    sem_num = n - com_num
    print(f"dias_por_semana com número: {fmt(com_num)} ({pct(com_num, n)}); sem número: {fmt(sem_num)} "
          f"(vazios {fmt(marcas['dias_por_semana_nao_informado'])} + 'todos' {fmt(todos)})")
    assert sem_num == marcas["dias_por_semana_nao_informado"] + todos

    # completude: as marcas não preenchem nada, então as medidas são as mesmas
    depois = medidas(df[COLUNAS_ORIG].apply(lambda s: s.str.strip() == ""))
    assert depois == antes
    print(f"células preenchidas: {pct(depois['celulas'] - depois['vazias'], depois['celulas'])}; "
          f"obrigatórias: {pct(depois['obr_cel'] - depois['obr_vazias'], depois['obr_cel'])}; "
          f"linhas completas: {fmt(depois['lin_comp'])} ({pct(depois['lin_comp'], n)}); "
          f"linhas completas nas obrigatórias: {fmt(depois['lin_comp_obr'])} ({pct(depois['lin_comp_obr'], n)})")

    df.to_csv(PROCESSADOS / "onboarding_padronizado.csv", index=False, encoding="utf-8")
    mostrar("onboarding_padronizado.csv regravado com marcas", df, n)

    L = ["# Completude do onboarding: marcas (Passo 3)", "",
         "Código: `src/marcas_completude_onboarding.py`. Nenhum vazio foi preenchido: as marcas só sinalizam a lacuna.", "",
         "## Marcas criadas", "", "| Marca | Contas marcadas | % das linhas | Regra |", "|---|---:|---:|---|",
         f"| `nivel_nao_informado` | {fmt(marcas['nivel_nao_informado'])} | {pct(marcas['nivel_nao_informado'], n)} | `nivel` vazio |",
         f"| `dias_por_semana_nao_informado` | {fmt(marcas['dias_por_semana_nao_informado'])} | {pct(marcas['dias_por_semana_nao_informado'], n)} | `dias_por_semana` vazio |",
         f"| `objetivo_sem_resposta` | {fmt(marcas['objetivo_sem_resposta'])} | {pct(marcas['objetivo_sem_resposta'], n)} | vazio (5.467) ou traço `-` (1.322) |",
         f"| `como_conheceu_sem_resposta` | {fmt(marcas['como_conheceu_sem_resposta'])} | {pct(marcas['como_conheceu_sem_resposta'], n)} | vazio (4.586) ou traço `-` (1.190) |",
         "", "## Completude (antes = depois, pois nada foi preenchido)", "",
         "| Medida | Valor |", "|---|---:|",
         f"| Células preenchidas (7 colunas) | {pct(depois['celulas'] - depois['vazias'], depois['celulas'])} |",
         f"| Só as 5 colunas não opcionais | {pct(depois['obr_cel'] - depois['obr_vazias'], depois['obr_cel'])} |",
         f"| Linhas sem nenhum vazio | {fmt(depois['lin_comp'])} ({pct(depois['lin_comp'], n)}) |",
         f"| Linhas sem vazio nas não opcionais | {fmt(depois['lin_comp_obr'])} ({pct(depois['lin_comp_obr'], n)}) |",
         "", "## Efeito da padronização em `dias_por_semana`", "",
         f"- Com número de 1 a 7: **{fmt(com_num)}** ({pct(com_num, n)}); antes, só as respostas escritas só como `N` eram diretamente numéricas.",
         f"- Sem número: **{fmt(sem_num)}** ({pct(sem_num, n)}) = {fmt(marcas['dias_por_semana_nao_informado'])} vazios + {fmt(todos)} `todos`.",
         f"- Linhas: {fmt(n)} antes e depois, um `user_id` por linha.", ""]
    SAIDAS.mkdir(exist_ok=True)
    (SAIDAS / "completude_marcas_onboarding.md").write_text("\n".join(L), encoding="utf-8")
    print("gravado saidas/completude_marcas_onboarding.md")


if __name__ == "__main__":
    main()
