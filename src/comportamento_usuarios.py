"""Comportamento por usuário até 30/06/2026 + grupos saiu × ficou (insumo da prática 12).

Grupos (passo 1 do roteiro):
- base  = pagantes ativos em 30/06/2026: assinatura iniciada até 30/06, sem fim ou com fim
  posterior a 30/06, plano pago (cortesia fora), conta de teste fora;
- saiu  = data_fim entre 01/07 e 30/09/2026;
- ficou = os demais (sem fim, ou fim depois de 30/09).
data_fim vem do retrato de 01/10, mas é fato histórico (a data em que acabou), não estado
reconstruível — não tem o vazamento da renovação (análise 11).

Features de comportamento — TODAS medidas até 30/06 (anti-vazamento):
- de dados/processados/atividades_limpa.parquet (gerada por preparar_atividades.py;
  exclui flag_impossivel): volume jan–jun, janelas 30/60/90 dias, recência, tendência
  mai–jun vs jan–abr, modalidades, uso de relógio;
- de uso_mensal.csv (meses 2026-01..2026-06, regime novo, zeros explícitos):
  sessões no app, dias ativos, minutos.

Saídas: dados/processados/comportamento_ate_30jun.parquet (1 linha por user da base;
fora do Git) e saidas/comportamento_saiu_ficou.md + .png (tabela comparativa e gráfico).
"""

from pathlib import Path

import pandas as pd

from utils import BRUTOS, PROCESSADOS, SAIDAS, contas_de_teste, mostrar

REF = pd.Timestamp("2026-06-30 23:59:59")  # tudo medido até aqui (Brasília)
FIM_JANELA = pd.Timestamp("2026-09-30")    # saiu = fim entre 01/07 e 30/09
TRATADA = PROCESSADOS / "atividades_limpa.parquet"


def fmt(n) -> str:
    return f"{n:,}".replace(",", ".")


def grupos() -> pd.DataFrame:
    a = pd.read_csv(BRUTOS / "assinaturas.csv",
                    usecols=["user_id", "plano_atual", "canal_cobranca", "inicio",
                             "data_fim", "motivo_fim"],
                    dtype=str)
    a["inicio"] = pd.to_datetime(a["inicio"])
    a["data_fim"] = pd.to_datetime(a["data_fim"])
    mostrar("assinaturas lidas", a)

    a = a[a["plano_atual"] != "cortesia"]
    mostrar("sem cortesias", a)
    a = a[~a["user_id"].isin(contas_de_teste())]
    mostrar("sem contas de teste (e-mail @vitaliza.com.br)", a)

    ativa_ref = (a["inicio"] <= REF) & (a["data_fim"].isna() | (a["data_fim"] > REF))
    base = a[ativa_ref].copy()
    mostrar("base: pagantes ativos em 30/06", base)

    base["grupo"] = "ficou"
    saiu = base["data_fim"].notna() & (base["data_fim"] <= FIM_JANELA)
    base.loc[saiu, "grupo"] = "saiu"
    print(f"[grupos] saiu: {fmt(int(saiu.sum()))} · ficou: {fmt(int((~saiu).sum()))} "
          f"(churn do trimestre: {100 * saiu.mean():.1f}%)")
    return base[["user_id", "grupo", "plano_atual", "canal_cobranca", "inicio", "data_fim"]]


def features_treinos(base_ids: pd.Series) -> pd.DataFrame:
    df = pd.read_parquet(TRATADA, columns=["user_id", "inicio", "tipo", "duracao_min",
                                           "origem", "flag_impossivel"])
    mostrar("atividades tratadas lidas", df)
    df = df[~df["flag_impossivel"]]
    mostrar("sem flag_impossivel", df, None)
    df = df[df["inicio"] <= REF]
    mostrar("até 30/06 (anti-vazamento)", df)
    df = df[df["user_id"].isin(set(base_ids))]
    mostrar("só da base de pagantes em 30/06", df)

    janela = lambda dias: df["inicio"] > REF - pd.Timedelta(days=dias)
    df["relogio"] = df["origem"].isin(["garmin", "apple_health"])
    df["mai_jun"] = df["inicio"] >= "2026-05-01"

    g = df.groupby("user_id")
    f = pd.DataFrame({
        "treinos_jan_jun": g.size(),
        "minutos_jan_jun": g["duracao_min"].sum().round(0),
        "treinos_30d": df[janela(30)].groupby("user_id").size(),
        "treinos_60d": df[janela(60)].groupby("user_id").size(),
        "treinos_90d": df[janela(90)].groupby("user_id").size(),
        "recencia_dias": (REF.normalize() - g["inicio"].max().dt.normalize()).dt.days,
        "n_modalidades": g["tipo"].nunique(),
        "pct_relogio": (100 * g["relogio"].mean()).round(1),
        "treinos_mai_jun": df[df["mai_jun"]].groupby("user_id").size(),
    })
    f[["treinos_30d", "treinos_60d", "treinos_90d", "treinos_mai_jun"]] = \
        f[["treinos_30d", "treinos_60d", "treinos_90d", "treinos_mai_jun"]].fillna(0).astype(int)
    # tendência: média mensal mai–jun ÷ média mensal jan–abr (>1 subindo, <1 caindo)
    jan_abr = (f["treinos_jan_jun"] - f["treinos_mai_jun"]) / 4
    f["tendencia"] = ((f["treinos_mai_jun"] / 2) / jan_abr.where(jan_abr > 0)).round(2)
    print(f"[resumo] 1 linha por usuário com treino: {fmt(len(f))}")
    return f.drop(columns=["treinos_mai_jun"])


def features_app(base_ids: pd.Series) -> pd.DataFrame:
    u = pd.read_csv(BRUTOS / "uso_mensal.csv", dtype={"user_id": str})
    mostrar("uso_mensal lido", u)
    u = u[u["mes"].between("2026-01", "2026-06")]
    mostrar("meses 2026-01..06 (regime novo, zeros explícitos)", u)
    u = u[u["user_id"].isin(set(base_ids))]
    mostrar("só da base", u)
    g = u.groupby("user_id")
    f = pd.DataFrame({
        "sessoes_app_mes": g["sessoes_app"].mean().round(1),
        "dias_ativos_mes": g["dias_ativos"].mean().round(1),
        "minutos_mes": g["minutos"].mean().round(0),
    })
    print(f"[resumo] 1 linha por usuário com uso: {fmt(len(f))}")
    return f


def main() -> None:
    base = grupos()
    treinos = features_treinos(base["user_id"])
    app = features_app(base["user_id"])

    antes = len(base)
    tab = base.merge(treinos, on="user_id", how="left").merge(app, on="user_id", how="left")
    mostrar("base + treinos + uso (junções 1:1 por user_id)", tab, antes)
    assert len(tab) == antes, "junção multiplicou linhas"
    zero = ["treinos_jan_jun", "minutos_jan_jun", "treinos_30d", "treinos_60d", "treinos_90d"]
    tab[zero] = tab[zero].fillna(0).astype(int)
    tab["sem_treino_jan_jun"] = tab["treinos_jan_jun"] == 0

    PROCESSADOS.mkdir(parents=True, exist_ok=True)
    destino = PROCESSADOS / "comportamento_ate_30jun.parquet"
    tab.to_parquet(destino, index=False)
    print(f"[saída] {destino}")

    # ---- comparação saiu × ficou ----
    feats = ["treinos_jan_jun", "treinos_90d", "treinos_30d", "recencia_dias", "tendencia",
             "n_modalidades", "pct_relogio", "sessoes_app_mes", "dias_ativos_mes", "minutos_mes"]
    med = tab.groupby("grupo")[feats].median().T
    med["diferença"] = (med["saiu"] - med["ficou"])
    pct_zero = tab.groupby("grupo")["sem_treino_jan_jun"].mean().mul(100).round(1)
    pct_rel = tab.assign(tem_rel=tab["pct_relogio"].gt(0)).groupby("grupo")["tem_rel"].mean().mul(100).round(1)
    print("\n=== medianas por grupo ===")
    print(med.to_string())
    print(f"\nsem nenhum treino jan–jun: saiu {pct_zero['saiu']}% × ficou {pct_zero['ficou']}%")
    print(f"tem treino de relógio: saiu {pct_rel['saiu']}% × ficou {pct_rel['ficou']}%")

    # gráfico: recência (a feature que mais separa costuma ser esta) — distribuição
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.5))
    cores = {"ficou": "#1D9E75", "saiu": "#D85A30"}
    for gr in ("ficou", "saiu"):
        s = tab.loc[(tab["grupo"] == gr) & (~tab["sem_treino_jan_jun"]), "recencia_dias"].clip(0, 180)
        axs[0].hist(s, bins=36, density=True, alpha=0.55, color=cores[gr], label=gr)
        s2 = tab.loc[tab["grupo"] == gr, "treinos_90d"].clip(0, 80)
        axs[1].hist(s2, bins=40, density=True, alpha=0.55, color=cores[gr], label=gr)
    axs[0].set_title("Dias desde o último treino em 30/06 (quem treinou)")
    axs[0].set_xlabel("dias"); axs[0].legend()
    axs[1].set_title("Treinos nos 90 dias até 30/06")
    axs[1].set_xlabel("treinos"); axs[1].legend()
    for ax in axs: ax.set_ylabel("densidade")
    fig.suptitle("Comportamento até 30/06 — saiu × ficou no 3º trimestre", y=1.02)
    fig.tight_layout()
    fig.savefig(SAIDAS / "comportamento_saiu_ficou.png", dpi=150, bbox_inches="tight")
    print(f"[saída] {SAIDAS / 'comportamento_saiu_ficou.png'}")

    linhas = [
        "# Comportamento até 30/06 × saída no 3º trimestre (insumo da prática 12)",
        "",
        "Gerado por `src/comportamento_usuarios.py` a partir da base tratada "
        "(`atividades_limpa.parquet`, sem `flag_impossivel`) e de `uso_mensal.csv` "
        "(meses 2026-01..06). Tudo medido até 30/06; saída = `data_fim` entre 01/07 e 30/09.",
        "",
        f"- Base: **{fmt(len(tab))}** pagantes ativos em 30/06 · saiu **{fmt((tab.grupo == 'saiu').sum())}** "
        f"({100 * (tab.grupo == 'saiu').mean():.1f}%) · ficou {fmt((tab.grupo == 'ficou').sum())}",
        f"- Sem nenhum treino em jan–jun: saiu {pct_zero['saiu']}% × ficou {pct_zero['ficou']}%",
        f"- Tem treino de relógio: saiu {pct_rel['saiu']}% × ficou {pct_rel['ficou']}%",
        "",
        "## Medianas por grupo",
        "",
        "| Feature | saiu | ficou | diferença |",
        "|---|---:|---:|---:|",
    ]
    for nome, r in med.iterrows():
        linhas.append(f"| {nome} | {r['saiu']:g} | {r['ficou']:g} | {r['diferença']:+g} |")
    linhas += ["", "![comparação](comportamento_saiu_ficou.png)", "",
               "As 3 frases (diz / não diz / próxima pergunta) ficam para a discussão em grupo "
               "(papéis Piloto/Auditor/Relator), conforme o roteiro."]
    (SAIDAS / "comportamento_saiu_ficou.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"[saída] {SAIDAS / 'comportamento_saiu_ficou.md'}")


if __name__ == "__main__":
    main()
