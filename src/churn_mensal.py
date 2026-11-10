"""Churn mensal oficial (B1): jan/2025 a set/2026, a partir de assinaturas.csv.

Churn do mês = perdas no mês / ativos no início do mês.
- ativo no início do mês: `inicio` antes do dia 1 e (sem `data_fim` ou `data_fim` >= dia 1);
- perda no mês: ativo no início com `data_fim` dentro do mês (assinaturas que começam e acabam
  no mesmo mês ficam fora da série).
Conferência com eventos_assinatura.csv (fuso para Brasília, decisão 13). Só lê os brutos (SHA-256
antes e depois). Saídas: dados/processados/churn_mensal.csv, saidas/churn_mensal.md e .png.
"""

import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils import contas_de_teste, para_brasilia

RAIZ = Path(__file__).resolve().parent.parent
ASSINATURAS = RAIZ / "dados" / "brutos" / "assinaturas.csv"
EVENTOS = RAIZ / "dados" / "brutos" / "eventos_assinatura.csv"
USUARIOS = RAIZ / "dados" / "brutos" / "usuarios.csv"
CSV = RAIZ / "dados" / "processados" / "churn_mensal.csv"
MD = RAIZ / "saidas" / "churn_mensal.md"
PNG = RAIZ / "saidas" / "churn_mensal.png"
MESES = list(pd.period_range("2025-01", "2026-09", freq="M"))
MOTIVOS = ["renovacao_desligada", "falha_pagamento", "chargeback", "reembolso"]
FIM_EVENTOS = ["assinatura_expirada", "chargeback", "reembolso"]  # cancelamento_web não é fim (decisão 15)


def sha256(*caminhos: Path) -> str:
    h = hashlib.sha256()
    for c in caminhos:
        with open(c, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
    return h.hexdigest()


def n(x) -> str:
    return f"{int(x):,}".replace(",", ".")


def pc(x) -> str:
    return f"{x:.1f}%".replace(".", ",")


def tabela(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    return "\n".join([cab, sep, *("| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False))])


def main() -> None:
    hash_antes = sha256(ASSINATURAS, EVENTOS, USUARIOS)
    out: list[str] = []
    L = out.append

    # 1. leitura e filtros
    a = pd.read_csv(ASSINATURAS, dtype=str, keep_default_na=False)
    n0 = len(a)
    ids0 = a["user_id"].nunique()
    print(f"[1] assinaturas: {n(n0)} linhas · {n(ids0)} user_id")
    cortesia = a["plano_atual"] == "cortesia"
    teste = a["user_id"].isin(contas_de_teste())
    print(f"[1] cortesia {n(cortesia.sum())} · conta de teste (e-mail) {n(teste.sum())} · ambos {n((cortesia & teste).sum())}")
    a = a[~(cortesia | teste)].copy()
    n1 = len(a)
    print(f"[1] sem cortesia/teste: {n(n0)} → {n(n1)}")
    a["inicio_d"] = pd.to_datetime(a["inicio"], format="%Y-%m-%d", errors="coerce")
    a["fim_d"] = pd.to_datetime(a["data_fim"].replace("", np.nan), format="%Y-%m-%d", errors="coerce")
    inicio_invalido = int(a["inicio_d"].isna().sum())
    fim_invalido = int((a["data_fim"].ne("") & a["fim_d"].isna()).sum())
    fim_antes_inicio = int((a["fim_d"] < a["inicio_d"]).sum())
    print(f"[1] datas inválidas: inicio {inicio_invalido} · data_fim {fim_invalido} · fim antes do início {fim_antes_inicio}")

    L("# Churn mensal oficial, jan/2025 a set/2026\n")
    L(f"Gerado por `src/churn_mensal.py`. Só leitura (SHA-256 conjunto de `assinaturas.csv`, `eventos_assinatura.csv` e `usuarios.csv` `{hash_antes[:16]}…` conferido antes e depois).\n")
    L("Definição: churn do mês = perdas no mês ÷ ativos no início do mês. Ativo no início = `inicio` antes do dia 1 e (sem `data_fim` ou `data_fim` ≥ dia 1). Perda = ativo no início com `data_fim` dentro do mês. Assinaturas que começam e terminam no mesmo mês ficam fora.\n")
    L("## 1. Linhas depois de cada passo\n")
    L(tabela(pd.DataFrame([
        ["assinaturas.csv", n(n0), f"{n(ids0)} user_id únicos"],
        ["sem as 60 contas de cortesia/teste (decisão 1)", n(n1), f"cortesia {n(cortesia.sum())}, teste por e-mail {n(teste.sum())}, ambos {n((cortesia & teste).sum())}"],
    ], columns=["passo", "linhas", "observação"])) + "\n")
    L(f"- Datas inválidas: `inicio` {n(inicio_invalido)}; `data_fim` {n(fim_invalido)}; `data_fim` antes de `inicio`: {n(fim_antes_inicio)}.\n")

    # 2. série mensal
    linhas = []
    for m in MESES:
        s, e = m.start_time, m.end_time.normalize() + pd.Timedelta(days=1)
        ativo = (a["inicio_d"] < s) & (a["fim_d"].isna() | (a["fim_d"] >= s))
        perdas = ativo & (a["fim_d"] >= s) & (a["fim_d"] < e)
        novos = (a["inicio_d"] >= s) & (a["inicio_d"] < e)
        mesmo = novos & (a["fim_d"] >= s) & (a["fim_d"] < e)
        fins_mes = (a["fim_d"] >= s) & (a["fim_d"] < e)
        r = dict(mes=str(m), ativos=int(ativo.sum()), perdas=int(perdas.sum()), novos=int(novos.sum()),
                 mesmo_mes=int(mesmo.sum()), fins=int(fins_mes.sum()))
        r["churn"] = 100 * r["perdas"] / r["ativos"]
        for mo in MOTIVOS:
            r[mo] = int((perdas & (a["motivo_fim"] == mo)).sum())
        r["outros_motivos"] = r["perdas"] - sum(r[mo] for mo in MOTIVOS)
        linhas.append(r)
    t = pd.DataFrame(linhas)
    CSV.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(CSV, index=False)
    ok_motivos = bool((t[MOTIVOS + ["outros_motivos"]].sum(axis=1) == t["perdas"]).all())
    media25 = t.loc[t["mes"] < "2026-01", "churn"].mean()
    media26 = t.loc[t["mes"] >= "2026-01", "churn"].mean()
    pond25 = 100 * t.loc[t["mes"] < "2026-01", "perdas"].sum() / t.loc[t["mes"] < "2026-01", "ativos"].sum()
    pond26 = 100 * t.loc[t["mes"] >= "2026-01", "perdas"].sum() / t.loc[t["mes"] >= "2026-01", "ativos"].sum()
    print(f"[2] {len(t)} meses · média simples 2025 {media25:.2f}% · 2026 {media26:.2f}% · ponderada {pond25:.2f}% / {pond26:.2f}%")

    f = pd.DataFrame({
        "mês": t["mes"], "ativos no início": t["ativos"].map(n), "perdas": t["perdas"].map(n), "churn": t["churn"].map(pc),
        "novos no mês": t["novos"].map(n), "começam e acabam no mês": t["mesmo_mes"].map(n),
        "renovação desligada": t["renovacao_desligada"].map(n), "falha de pagamento": t["falha_pagamento"].map(n),
        "chargeback": t["chargeback"].map(n), "reembolso": t["reembolso"].map(n)})
    L("## 2. Série mensal (21 meses)\n")
    L(tabela(f) + "\n")
    L(f"Perdas por motivo somam as perdas de cada mês: {'✔' if ok_motivos else '✘'} (motivos fora da lista: {n(t['outros_motivos'].sum())}).\n")

    # 3. conferência com o case
    def v(mes, col):
        return int(t.loc[t["mes"] == mes, col].iloc[0])

    fins_jun_set = int(t.loc[t["mes"].between("2026-06", "2026-09"), "fins"].sum())
    perdas_jun_set = int(t.loc[t["mes"].between("2026-06", "2026-09"), "perdas"].sum())
    ativos_30set = int(((a["inicio_d"] <= "2026-09-30") & (a["fim_d"].isna() | (a["fim_d"] > "2026-09-30"))).sum())
    refs = [
        ["ativos no início de jan/2025", "8.540", n(v("2025-01", "ativos"))],
        ["churn médio 2025 (média simples dos 12 meses)", "5,6%", pc(media25)],
        ["churn médio jan–set/2026 (média simples)", "6,6%", pc(media26)],
        ["abril/2026: perdas sobre ativos", "1.154 sobre 14.237 (8,1%)", f"{n(v('2026-04', 'perdas'))} sobre {n(v('2026-04', 'ativos'))} ({pc(t.loc[t['mes'] == '2026-04', 'churn'].iloc[0])})"],
        ["agosto/2026", "5,9%", pc(t.loc[t["mes"] == "2026-08", "churn"].iloc[0])],
        ["setembro/2026", "5,0%", pc(t.loc[t["mes"] == "2026-09", "churn"].iloc[0])],
        ["ativos no início de set/2026", "14.319", n(v("2026-09", "ativos"))],
        ["perdas jun a set (série)", "3.362", n(perdas_jun_set)],
        ["fins de assinatura jun a set", "3.389", n(fins_jun_set)],
        ["ativos em 30/09/2026", "14.753", n(ativos_30set)],
    ]
    L("## 3. Conferência com o case\n")
    L(tabela(pd.DataFrame(refs, columns=["medida", "referência do case", "calculado"])) + "\n")
    L(f"- Churn ponderado (perdas ÷ ativos somados): 2025 {pc(pond25)}; jan–set/2026 {pc(pond26)}.")
    L(f"- Diferença entre fins e perdas de jun a set: {n(fins_jun_set - perdas_jun_set)} (assinaturas que começam e terminam no mesmo mês: {n(t.loc[t['mes'].between('2026-06', '2026-09'), 'mesmo_mes'].sum())}).\n")
    for lin in refs:
        print(f"[3] {lin[0]}: case {lin[1]} · calculado {lin[2]}")

    # 4. conferência com eventos
    ev = pd.read_csv(EVENTOS, dtype=str, keep_default_na=False)
    ev["quando"] = para_brasilia(ev["data_hora"])
    fim_ev = (ev[ev["evento"].isin(FIM_EVENTOS)].dropna(subset=["quando"]).sort_values("quando")
              .groupby("user_id").agg(data_evento=("quando", "last"), tipo_evento=("evento", "last")))
    enc = a[a["fim_d"].notna() & (a["fim_d"] >= "2024-07-01")].merge(fim_ev, left_on="user_id", right_index=True, how="left")
    sem_ev = enc["data_evento"].isna()
    enc["dif_dias"] = (enc["data_evento"].dt.normalize() - enc["fim_d"]).dt.days
    mesmo_dia = (enc["dif_dias"] == 0)
    mesmo_mes = (enc["data_evento"].dt.to_period("M") == enc["fim_d"].dt.to_period("M")) & ~mesmo_dia
    outro = ~sem_ev & ~mesmo_dia & ~mesmo_mes
    print(f"[4] encerradas desde 01/07/2024: {n(len(enc))} · com evento de fim {n((~sem_ev).sum())} · mesmo dia {n(mesmo_dia.sum())} · mesmo mês {n(mesmo_mes.sum())} · outro mês {n(outro.sum())} · sem evento {n(sem_ev.sum())}")
    L("## 4. Conferência com os eventos (desde 01/07/2024, fuso em Brasília)\n")
    L(f"Para cada assinatura encerrada com `data_fim` desde 01/07/2024 ({n(len(enc))}), comparo `data_fim` com o último evento de fim (`assinatura_expirada`, `chargeback` ou `reembolso`; `cancelamento_web` não conta, decisão 15).\n")
    por_motivo = []
    for mo in MOTIVOS:
        g = enc[enc["motivo_fim"] == mo]
        sm = g["data_evento"].isna()
        d0 = g["dif_dias"] == 0
        dm = (g["data_evento"].dt.to_period("M") == g["fim_d"].dt.to_period("M")) & ~d0
        por_motivo.append([mo, n(len(g)), n(d0.sum()), n(dm.sum()), n((~sm & ~d0 & ~dm).sum()), n(sm.sum())])
    por_motivo.append(["total", n(len(enc)), n(mesmo_dia.sum()), n(mesmo_mes.sum()), n(outro.sum()), n(sem_ev.sum())])
    L(tabela(pd.DataFrame(por_motivo, columns=["motivo_fim", "encerradas", "mesmo dia", "mesmo mês, outro dia", "outro mês", "sem evento de fim"])) + "\n")
    L(f"- Diferença em dias (evento − `data_fim`) nas que têm evento: mediana {enc['dif_dias'].median():.0f}, mínimo {enc['dif_dias'].min():.0f}, máximo {enc['dif_dias'].max():.0f}.")
    L(f"- Soma conferida: {n(mesmo_dia.sum() + mesmo_mes.sum() + outro.sum() + sem_ev.sum())} = {n(len(enc))} {'✔' if mesmo_dia.sum() + mesmo_mes.sum() + outro.sum() + sem_ev.sum() == len(enc) else '✘'}.")
    L("- As divergências são só descritas; nada foi corrigido. `data_fim` de `assinaturas.csv` é a fonte da série.\n")

    # 5. alertas
    L("## 5. Alertas\n")
    L("- `assinaturas.csv` é um retrato de 01/10/2026: `inicio`, `data_fim` e `motivo_fim` servem para o histórico, mas `plano_atual` e `canal_cobranca` são os valores de hoje. Cuidado ao cruzar o churn com plano e canal (B3).")
    L(f"- `data_fim` mais antigo: {a['fim_d'].min():%d/%m/%Y}; o log de eventos começa em 01/07/2024.\n")

    # 6. decisões propostas
    L("## 6. Decisões propostas (formato do `decisoes.md`, não gravadas)\n")
    L("| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |")
    L("|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|")
    L(f"| 31 | 09/11/2026 | assinaturas.csv | definição do churn mensal | calcular a série de `inicio`/`data_fim` de `assinaturas.csv`, sem as contas de cortesia/teste; toda `data_fim` conta como perda (renovação desligada, falha de pagamento, chargeback, reembolso) | reproduz os números do case (8.540 ativos em jan/2025; abril/2026 = 1.154 sobre 14.237) | {n(n0)} → {n(n1)} assinaturas; 21 meses; {n(t['perdas'].sum())} perdas |")
    L(f"| 32 | 09/11/2026 | eventos_assinatura.csv | `data_fim` e o evento de fim nem sempre caem no mesmo dia | usar os eventos só para conferir, sem corrigir `data_fim` | divergência medida na seção 4: mesmo dia {n(mesmo_dia.sum())}, mesmo mês {n(mesmo_mes.sum())}, outro mês {n(outro.sum())}, sem evento {n(sem_ev.sum())} de {n(len(enc))} | 0 linhas alteradas |")
    estado = "inalterados" if sha256(ASSINATURAS, EVENTOS, USUARIOS) == hash_antes else "ALTERADOS"
    L(f"\n---\nConferência: brutos {estado}.")
    MD.write_text("\n".join(out), encoding="utf-8")

    # gráfico
    fundo, tinta, suave, azul = "#fcfcfb", "#0b0b0b", "#52514e", "#2a78d6"
    fig, ax = plt.subplots(figsize=(11, 4.6), facecolor=fundo)
    ax.set_facecolor(fundo)
    x = np.arange(len(t))
    ax.plot(x, t["churn"], color=azul, lw=2, marker="o", ms=4)
    ax.hlines(5.6, -0.4, 11.4, color=suave, lw=1, ls="--")
    ax.hlines(6.6, 11.6, len(t) - 0.6, color=suave, lw=1, ls="--")
    ax.text(0, 0.6, "tracejado: referência 2025 = 5,6%", fontsize=8, color=suave, va="bottom")
    ax.text(12, 0.6, "tracejado: referência jan–set/2026 = 6,6%", fontsize=8, color=suave, va="bottom")
    i_abr = int(t.index[t["mes"] == "2026-04"][0])
    ax.annotate("abr/2026: 8,1%\n(1.154 de 14.237)", (i_abr, t.loc[i_abr, "churn"]), xytext=(i_abr - 0.2, t.loc[i_abr, "churn"] + 0.9),
                fontsize=8, color=tinta, ha="center", arrowprops=dict(arrowstyle="-", color=suave, lw=0.8))
    ax.set_xticks(x[::2])
    ax.set_xticklabels([m[2:] for m in t["mes"]][::2], fontsize=8, color=suave, rotation=45)
    ax.set_ylim(0, 10)
    ax.set_ylabel("churn mensal (% dos ativos no início do mês)", fontsize=9, color=suave)
    ax.set_title("Churn mensal, jan/2025 a set/2026", fontsize=12, color=tinta, loc="left")
    ax.tick_params(colors=suave, labelsize=8)
    ax.grid(axis="y", color="#e6e5e0", lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c9c8c2")
    fig.tight_layout()
    fig.savefig(PNG, dpi=150, facecolor=fundo)

    print(f"brutos {estado} · 21 meses {'ok' if len(t) == 21 else 'ERRO'} · motivos somam perdas {'ok' if ok_motivos else 'ERRO'}")
    print(f"escrito: {CSV.relative_to(RAIZ)} · {MD.relative_to(RAIZ)} · {PNG.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
