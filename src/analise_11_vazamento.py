"""Análise 11: situação da renovação em 31/07/2026 pelos eventos. Colaborador 1.

Arquivos: assinaturas.csv, usuarios.csv e eventos_assinatura.csv (só leitura).
Mede o erro de usar o retrato de 01/10 (vazamento de dados).

Rodar da raiz do projeto:  python -I src/analise_11_vazamento.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import BRUTOS, PROCESSADOS, SAIDAS, contas_de_teste, mostrar, para_brasilia  # noqa: E402

DATA_REF = pd.Timestamp("2026-07-31 23:59:59")  # fim do dia 31/07, Brasília
INICIO_LOG = pd.Timestamp("2024-07-01")  # antes disso não há evento de início
DESLIGA = "renovacao_automatica_desligada"
RELIGA = "renovacao_automatica_religada"
WEB = "cancelamento_web"
NAO_ASSINAVA, DESLIGADA, LIGADA = "ainda_nao_assinava", "renovacao_desligada", "renovacao_ligada"


def classificar(ass: pd.DataFrame, ev: pd.DataFrame, web_desliga: bool) -> pd.Series:
    """Situação de cada conta em 31/07 (índice = user_id)."""
    tipos = {DESLIGA, RELIGA} | ({WEB} if web_desliga else set())
    ult = (
        ev[ev["evento"].isin(tipos)]
        .sort_values(["user_id", "data_hora_br"], kind="stable")
        .groupby("user_id")["evento"].last()
    )
    a = ass.set_index("user_id")
    ultimo = ult.reindex(a.index)
    sit = pd.Series(LIGADA, index=a.index)  # sem evento até 31/07 -> ligada
    sit[ultimo.isin({DESLIGA, WEB})] = DESLIGADA
    sit[a["inicio"] > DATA_REF.normalize()] = NAO_ASSINAVA
    return sit


def main() -> None:
    # 1. assinaturas e contas de teste
    ass = pd.read_csv(BRUTOS / "assinaturas.csv", dtype=str)
    mostrar("assinaturas.csv", ass)
    teste = contas_de_teste()
    print(f"contas de teste (usuarios.csv): {len(teste)}")

    # 2. filtro: ativas, renovação desligada, sem testes
    n0 = len(ass)
    ass = mostrar("status_atual = ativa", ass[ass["status_atual"] == "ativa"], n0)
    n0 = len(ass)
    ass = mostrar("renovacao_automatica = nao", ass[ass["renovacao_automatica"] == "nao"], n0)
    n0 = len(ass)
    ass = mostrar("sem contas de teste", ass[~ass["user_id"].isin(teste)], n0)
    assert len(ass) == 2250, f"esperado 2.250, veio {len(ass)}"
    assert ass["user_id"].is_unique
    ass["inicio"] = pd.to_datetime(ass["inicio"])
    print(ass["plano_atual"].value_counts().to_dict())

    # 3. eventos: fuso e corte
    ev = pd.read_csv(BRUTOS / "eventos_assinatura.csv", dtype=str)
    mostrar("eventos_assinatura.csv", ev)
    print(f"  com Z (UTC): {ev['data_hora'].str.endswith('Z').sum():,} | sem fuso: {(~ev['data_hora'].str.endswith('Z')).sum():,}".replace(",", "."))
    ev["data_hora_br"] = para_brasilia(ev["data_hora"])
    assert ev["data_hora_br"].notna().all(), "há data_hora que não foi lida"
    # fronteira: eventos que mudam de dia ao converter
    dia_bruto = pd.to_datetime(ev["data_hora"].str[:10])
    mudou = (dia_bruto != ev["data_hora_br"].dt.normalize()).sum()
    print(f"eventos cujo dia muda ao converter para Brasília: {mudou:,}".replace(",", "."))

    # 4. reduzir: só as 2.250 contas e eventos até 31/07 (Brasília)
    n0 = len(ev)
    ev = mostrar("eventos das 2.250 contas", ev[ev["user_id"].isin(ass["user_id"])], n0)
    print(f"  contas com algum evento: {ev['user_id'].nunique():,}".replace(",", "."))
    n0 = len(ev)
    ev = mostrar("eventos até 31/07/2026 23:59:59 (Brasília)", ev[ev["data_hora_br"] <= DATA_REF], n0)
    print(f"  cancelamento_web nas 2.250 (todo o período): {(ev['evento'] == WEB).sum()} até 31/07")

    # 5. classificar (versão principal: só desligada/religada; alternativa: web também desliga)
    sit = classificar(ass, ev, web_desliga=False)
    sit_web = classificar(ass, ev, web_desliga=True)

    # 6. junção pela esquerda: continua 2.250, um user_id por linha
    saida = ass[["user_id", "plano_atual", "canal_cobranca", "inicio"]].merge(
        sit.rename("situacao_31jul"), left_on="user_id", right_index=True, how="left"
    ).merge(sit_web.rename("situacao_31jul_web_desliga"), left_on="user_id", right_index=True, how="left")
    mostrar("junção com a situação (esquerda)", saida, len(ass))
    assert len(saida) == 2250 and saida["user_id"].is_unique and saida["situacao_31jul"].notna().all()
    saida["sem_evento_inicio"] = saida["inicio"] < INICIO_LOG
    PROCESSADOS.mkdir(parents=True, exist_ok=True)
    saida.to_csv(PROCESSADOS / "situacao_renovacao_31jul.csv", index=False)

    vc = saida["situacao_31jul"].value_counts()
    vc_web = saida["situacao_31jul_web_desliga"].value_counts()
    print("\nSituação em 31/07 (principal):", vc.to_dict(), "soma", vc.sum())
    print("Variante (cancelamento_web desliga):", vc_web.to_dict())
    erro = len(saida) - vc.get(DESLIGADA, 0)
    print(f"Retrato de 01/10 acerta {vc.get(DESLIGADA, 0)}; erra {erro} ({erro / len(saida):.1%})")
    print("Início antes de 01/07/2024:", int(saida["sem_evento_inicio"].sum()),
          "->", saida.loc[saida["sem_evento_inicio"], "situacao_31jul"].value_counts().to_dict())
    print("Por plano:\n", pd.crosstab(saida["plano_atual"], saida["situacao_31jul"]))
    print("Por canal:\n", pd.crosstab(saida["canal_cobranca"], saida["situacao_31jul"]))

    # três contas para conferir à mão: uma de cada situação + multi-desligamento + pré-2024
    deslig = ev[ev["evento"] == DESLIGA].groupby("user_id").size()
    amostra = {
        "desligada (vários desligamentos)": saida[(saida["situacao_31jul"] == DESLIGADA) & saida["user_id"].isin(deslig[deslig > 1].index)],
        "ligada, começou antes de 01/07/2024": saida[(saida["situacao_31jul"] == LIGADA) & saida["sem_evento_inicio"]],
        "ainda não assinava": saida[saida["situacao_31jul"] == NAO_ASSINAVA],
    }
    for nome, d in amostra.items():
        uid = d.sort_values("user_id")["user_id"].iloc[0]
        print(f"\n[conta para conferir] {nome}: {uid}")
        print(ev[ev["user_id"] == uid].sort_values("data_hora_br")[["data_hora", "data_hora_br", "evento"]].tail(6).to_string(index=False))
        print("  inicio:", saida.loc[saida["user_id"] == uid, "inicio"].iloc[0].date())

    SAIDAS.mkdir(exist_ok=True)


if __name__ == "__main__":
    main()
