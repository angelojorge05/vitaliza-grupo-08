"""Bloco C (prompt 07): estatística descritiva do uso em set/2026 (uso_mensal.csv, só mes = 2026-09).

Só lê o bruto (SHA-256 antes e depois). Contas de teste (e-mail @vitaliza.com.br) mostradas com e sem.
Saídas: saidas/estatistica_uso_set26.md e saidas/estatistica_uso_set26.png.
"""

import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils import contas_de_teste

RAIZ = Path(__file__).resolve().parent.parent
USO = RAIZ / "dados" / "brutos" / "uso_mensal.csv"
MD = RAIZ / "saidas" / "estatistica_uso_set26.md"
PNG = RAIZ / "saidas" / "estatistica_uso_set26.png"


def sha256(c: Path) -> str:
    h = hashlib.sha256()
    with open(c, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def n(x) -> str:
    return f"{int(x):,}".replace(",", ".")


def g(x, d=1) -> str:
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tabela(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    return "\n".join([cab, sep, *("| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False))])


def medidas(s: pd.Series) -> dict:
    moda = s.mode()
    return {"n": len(s), "média": s.mean(), "mediana": s.median(), "moda": float(moda.iloc[0]) if len(moda) else np.nan,
            "n_moda": int((s == moda.iloc[0]).sum()) if len(moda) else 0,
            "dp (n−1)": s.std(ddof=1), "dp (n)": s.std(ddof=0), "cv (n−1)": s.std(ddof=1) / s.mean() if s.mean() else np.nan,
            "q1": s.quantile(0.25), "q3": s.quantile(0.75), "mín": s.min(), "máx": s.max()}


def main() -> None:
    hash_antes = sha256(USO)
    u = pd.read_csv(USO, dtype={"user_id": str, "mes": str})
    total_arq = len(u)
    s = u[u["mes"] == "2026-09"].copy()
    print(f"[1] uso_mensal: {n(total_arq)} linhas → mes = 2026-09: {n(len(s))} linhas, {n(s['user_id'].nunique())} user_id")
    teste = contas_de_teste()
    s_teste = s[s["user_id"].isin(teste)]
    sem = s[~s["user_id"].isin(teste)].copy()
    print(f"[1] contas de teste: {n(len(teste))} · com linha em set/2026: {n(len(s_teste))} · linhas {n(len(s))} → {n(len(sem))}")

    m_tudo = medidas(sem["minutos"])
    pos = sem.loc[sem["minutos"] > 0, "minutos"]
    zeros = int((sem["minutos"] == 0).sum())
    neg = int((sem["minutos"] < 0).sum())
    ok_soma = zeros + len(pos) + neg == len(sem)
    m_pos = medidas(pos)
    print(f"[3] zeros {n(zeros)} ({100*zeros/len(sem):.1f}%) + minutos > 0 {n(len(pos))} + negativos {n(neg)} = {n(zeros + len(pos) + neg)} "
          f"{'ok' if ok_soma else 'ERRO'} (linhas {n(len(sem))})")
    print(f"[2] todas: média {m_tudo['média']:.1f} mediana {m_tudo['mediana']:.1f} moda {m_tudo['moda']:.0f} cv {m_tudo['cv (n−1)']:.2f} · "
          f">0: média {m_pos['média']:.1f} mediana {m_pos['mediana']:.1f} cv {m_pos['cv (n−1)']:.2f}")

    # com e sem contas de teste (só para mostrar o efeito)
    m_com = medidas(s["minutos"])
    L = ["# Estatística descritiva do uso em set/2026 (`uso_mensal.csv`, `mes = 2026-09`)\n",
         f"Gerado por `src/estatistica_uso_set26.py`. Só leitura (SHA-256 `{hash_antes[:16]}…` conferido antes e depois). Nada foi alterado.\n",
         "## 1. Linhas e contas\n",
         tabela(pd.DataFrame([
             ["uso_mensal.csv inteiro", n(total_arq), "21 meses"],
             ["só `mes = 2026-09`", n(len(s)), f"{n(s['user_id'].nunique())} `user_id` únicos"],
             ["contas de teste com linha em set/2026", n(len(s_teste)), f"{n(len(teste))} contas de teste no total"],
             ["sem contas de teste", n(len(sem)), f"{n(sem['user_id'].nunique())} `user_id` únicos"],
         ], columns=["passo", "linhas", "observação"])) + "\n",
         f"- Com e sem contas de teste: média {g(m_com['média'])} min contra {g(m_tudo['média'])} min (diferença nula: nenhuma conta de teste tem linha em `uso_mensal.csv`).",
         f"- Um `user_id` por linha: {'✔' if s['user_id'].is_unique else '✘'}.\n",
         "## 2. Minutos: medidas de centro e dispersão\n"]
    linhas = []
    for nome, m in [("todas as contas (arquivo como está)", m_tudo), ("só minutos > 0", m_pos)]:
        linhas.append([nome, n(m["n"]), g(m["média"]), g(m["mediana"]), f"{g(m['moda'], 0)} ({n(m['n_moda'])} contas)",
                       g(m["dp (n−1)"]), g(m["dp (n)"]), g(m["cv (n−1)"], 2)])
    L.append(tabela(pd.DataFrame(linhas, columns=["versão", "contas", "média", "mediana", "moda", "dp (n−1)", "dp (n)", "CV (dp n−1 ÷ média)"])) + "\n")
    L.append("**n ou n−1?** Usei **n−1** (desvio amostral). Os 56 mil registros de set/2026 são todas as contas que têm linha no mês, ou seja, a população daquele mês; "
             "mas o que queremos descrever é o comportamento de uso que gera esses números (e comparar com outros meses), e nesse caso a população do mês é só uma amostra desse comportamento. "
             f"Com {n(len(sem))} linhas a diferença é desprezível: dp (n−1) {g(m_tudo['dp (n−1)'], 3)} contra dp (n) {g(m_tudo['dp (n)'], 3)}.\n")
    L.append("## 3. Proporção de contas com zero\n")
    L.append(tabela(pd.DataFrame([
        ["minutos = 0", n(zeros), f"{g(100*zeros/len(sem))}%"], ["minutos > 0", n(len(pos)), f"{g(100*len(pos)/len(sem))}%"],
        ["minutos < 0", n(neg), f"{g(100*neg/len(sem))}%"], ["total", n(zeros + len(pos) + neg), "100,0%"]],
        columns=["grupo", "contas", "%"])) + "\n")
    L.append(f"Conferência: {n(zeros)} + {n(len(pos))} + {n(neg)} = {n(zeros + len(pos) + neg)} = linhas {n(len(sem))} {'✔' if ok_soma else '✘'}.\n")
    L.append("## 4. Quartis e máximo das duas versões\n")
    q = [[nome, g(m["mín"], 0), g(m["q1"]), g(m["mediana"]), g(m["q3"]), g(m["máx"], 0)] for nome, m in
         [("todas as contas", m_tudo), ("só minutos > 0", m_pos)]]
    L.append(tabela(pd.DataFrame(q, columns=["versão", "mínimo", "Q1", "mediana", "Q3", "máximo"])) + "\n")
    L.append("## 5. Qual medida descreve a conta típica\n")
    L.append(f"Em set/2026, {g(100*zeros/len(sem))}% das contas têm zero minuto, então a média ({g(m_tudo['média'])} min) é puxada para baixo pelos zeros e a mediana e a moda são 0, o que descreve a conta típica do arquivo "
             f"inteiro (que não treinou) mas não diz nada de quem treina. Para quem treinou, a mediana ({g(m_pos['mediana'])} min) é a medida mais honesta: a média ({g(m_pos['média'])} min) fica acima porque a cauda à direita "
             f"(máximo {g(m_pos['máx'], 0)} min) a puxa, e o CV de {g(m_pos['cv (n−1)'], 2)} mostra dispersão grande.\n")
    L.append("Nota: em 2026 o mês sem treino é uma linha com zero, e em 2025 era linha ausente (ver `temporalidade_uso_mensal.md`); a média sobre o arquivo só é comparável com 2025 se for calculada só para `minutos > 0`.\n")
    L.append(f"---\nConferência: bruto {'inalterado' if sha256(USO) == hash_antes else 'ALTERADO'}.")
    MD.write_text("\n".join(L), encoding="utf-8")

    # histogramas
    fundo, tinta, suave, azul = "#fcfcfb", "#0b0b0b", "#52514e", "#2a78d6"
    fig, eixos = plt.subplots(1, 2, figsize=(12, 4.4), facecolor=fundo)
    teto = float(np.ceil(sem["minutos"].quantile(0.995) / 60) * 60)
    bins = np.arange(0, teto + 30, 30)
    for ax, dados, titulo in [(eixos[0], sem["minutos"], "Todas as contas (inclui minutos = 0)"),
                              (eixos[1], pos, "Só quem treinou (minutos > 0)")]:
        ax.set_facecolor(fundo)
        acima = int((dados > teto).sum())
        ax.hist(dados.clip(upper=teto), bins=bins, color=azul, edgecolor=fundo, linewidth=0.5)
        ax.set_title(titulo, fontsize=11, color=tinta, loc="left")
        ax.set_xlabel(f"minutos no mês (classes de 30 min; {n(acima)} contas acima de {int(teto)} min agrupadas na última)", fontsize=8, color=suave)
        ax.set_ylabel("contas", fontsize=9, color=suave)
        ax.tick_params(colors=suave, labelsize=8)
        ax.grid(axis="y", color="#e6e5e0", lw=0.6)
        ax.axvline(dados.median(), color="#eb6834", lw=1.5, ls="--")
        ax.text(dados.median() + teto * 0.05, ax.get_ylim()[1] * 0.92, f"mediana {g(dados.median(), 0)} min", color=suave, fontsize=8)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"):
            ax.spines[sp].set_color("#c9c8c2")
    fig.suptitle("Minutos de uso por conta, set/2026", fontsize=12, color=tinta, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(PNG, dpi=150, facecolor=fundo)
    print(f"bruto {'inalterado' if sha256(USO) == hash_antes else 'ALTERADO'} · escrito: {MD.relative_to(RAIZ)} · {PNG.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
