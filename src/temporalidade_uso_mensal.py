"""Temporalidade de dados/brutos/uso_mensal.csv (prompt 05): como o mês sem treino é registrado.

Só mede e explica; nada é corrigido. Contas de teste (e-mail @vitaliza.com.br em usuarios.csv)
são excluídas antes das médias, com a contagem mostrada. Lê o bruto (SHA-256 antes e depois)
e grava saidas/temporalidade_uso_mensal.md e .png.
"""

import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
USO = RAIZ / "dados" / "brutos" / "uso_mensal.csv"
USUARIOS = RAIZ / "dados" / "brutos" / "usuarios.csv"
MD = RAIZ / "saidas" / "temporalidade_uso_mensal.md"
PNG = RAIZ / "saidas" / "temporalidade_uso_mensal.png"
LINHAS_DICIONARIO = 591_662
MESES = [str(m) for m in pd.period_range("2025-01", "2026-09", freq="M")]


def sha256(*caminhos: Path) -> str:
    h = hashlib.sha256()
    for c in caminhos:
        with open(c, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
    return h.hexdigest()


def n(x) -> str:
    return f"{int(x):,}".replace(",", ".")


def d1(x) -> str:
    return "—" if pd.isna(x) else f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pc(a, b) -> str:
    return f"{100 * a / b:.1f}%".replace(".", ",")


def tabela(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    return "\n".join([cab, sep, *("| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False))])


def main() -> None:
    hash_antes = sha256(USO, USUARIOS)
    u = pd.read_csv(USO, dtype=str, keep_default_na=False)
    u["minutos"] = pd.to_numeric(u["minutos"], errors="raise")
    total = len(u)
    print(f"[0] uso_mensal: {n(total)} linhas · {u['mes'].nunique()} meses · {n(u['user_id'].nunique())} contas")

    # contas de teste
    us = pd.read_csv(USUARIOS, dtype=str, keep_default_na=False)
    teste = set(us.loc[us["email"].str.strip().str.lower().str.endswith("@vitaliza.com.br"), "user_id"])
    linhas_teste = int(u["user_id"].isin(teste).sum())
    contas_teste_no_uso = u.loc[u["user_id"].isin(teste), "user_id"].nunique()
    por_mes_total = u.groupby("mes").size()
    ok_total = int(por_mes_total.sum()) == total == LINHAS_DICIONARIO and list(por_mes_total.index) == MESES
    u = u[~u["user_id"].isin(teste)].copy()
    print(f"[filtro] contas de teste em usuarios.csv: {n(len(teste))} · aparecem em uso_mensal: {n(contas_teste_no_uso)} "
          f"({n(linhas_teste)} linhas) · linhas {n(total)} → {n(len(u))}")

    # tabela por mês
    linhas = []
    for mes in MESES:
        s = u[u["mes"] == mes]
        pos = s.loc[s["minutos"] > 0, "minutos"]
        zeros = int((s["minutos"] == 0).sum())
        rep = int(s.duplicated(["user_id", "mes"]).sum())
        linhas.append(dict(mes=mes, linhas=len(s), contas=s["user_id"].nunique(), zeros=zeros,
                           pct_zero=100 * zeros / len(s), media_arq=s["minutos"].mean(), mediana_arq=s["minutos"].median(),
                           media_pos=pos.mean(), mediana_pos=pos.median(), repetidas=rep))
    t = pd.DataFrame(linhas)
    soma_linhas = int(t["linhas"].sum())
    ok_cobre = len(t) == 21 and (t["linhas"] > 0).all()
    dup_total = int(u.duplicated(["user_id", "mes"]).sum())
    print(f"[tabela] {len(t)} meses · soma das linhas {n(soma_linhas)} (+ {n(linhas_teste)} de teste = {n(soma_linhas + linhas_teste)}) "
          f"· linhas repetidas user_id+mês: {n(dup_total)}")

    a25 = t[t["mes"] < "2026-01"]
    a26 = t[t["mes"] >= "2026-01"]
    z25, l25 = int(a25["zeros"].sum()), int(a25["linhas"].sum())
    z26, l26 = int(a26["zeros"].sum()), int(a26["linhas"].sum())
    print(f"[virada] zeros 2025: {n(z25)} de {n(l25)} · 2026: {n(z26)} de {n(l26)} ({pc(z26, l26)})")
    print(f"[virada] linhas/mês: 2025 {n(l25/12)} · 2026 {n(l26/9)} · média sobre linhas>0: 2025 {d1(a25['media_pos'].mean())} · 2026 {d1(a26['media_pos'].mean())}")

    # tabela formatada
    f = pd.DataFrame({
        "mês": t["mes"], "linhas": t["linhas"].map(n), "contas": t["contas"].map(n),
        "minutos = 0": t["zeros"].map(n), "% zero": [pc(a, b) for a, b in zip(t["zeros"], t["linhas"])],
        "média (arquivo)": t["media_arq"].map(d1), "mediana (arquivo)": t["mediana_arq"].map(d1),
        "média (>0)": t["media_pos"].map(d1), "mediana (>0)": t["mediana_pos"].map(d1),
        "repetidas": t["repetidas"].map(n)})

    out: list[str] = []
    p = out.append
    p("# Temporalidade de uso_mensal.csv: como o mês sem treino é registrado\n")
    p(f"Gerado por `src/temporalidade_uso_mensal.py`. Só leitura: SHA-256 conjunto de `uso_mensal.csv` e `usuarios.csv` `{hash_antes[:16]}…` conferido antes e depois. Nada foi corrigido.\n")
    p("## 1. Contagens do meio do caminho\n")
    p(f"- Linhas no arquivo: **{n(total)}** ({n(len(por_mes_total))} meses, de {por_mes_total.index[0]} a {por_mes_total.index[-1]}); soma das linhas por mês = total = dicionário {'✔' if ok_total else '✘'}.")
    p(f"- Contas de teste (`@vitaliza.com.br` em `usuarios.csv`): **{n(len(teste))}**. Delas, **{n(contas_teste_no_uso)}** aparecem em `uso_mensal.csv` ({n(linhas_teste)} linhas). "
      f"Linhas depois de excluí-las: {n(total)} → **{n(len(u))}**.")
    p(f"- Soma das linhas por mês na tabela abaixo: **{n(soma_linhas)}**; a tabela cobre {len(t)} meses {'✔' if ok_cobre and len(t) == 21 else '✘'}.")
    p(f"- Linhas repetidas para o mesmo `user_id` e mês: **{n(dup_total)}**.\n")
    p("## 2. Tabela por mês (sem as contas de teste)\n")
    p("\"Arquivo\" = todas as linhas como estão; \">0\" = só as linhas com `minutos` > 0. Minutos em minutos por conta-mês.\n")
    p(tabela(f) + "\n")

    # explicação
    pos25, pos26 = (l25 - z25) / 12, (l26 - z26) / 9
    p("## 3. A virada de 2025 para 2026\n")
    p(f"- **2025 (jan a dez):** {n(z25)} linhas com `minutos = 0` em {n(l25)}. O mês sem treino **não aparece**: a conta simplesmente não tem linha. "
      f"São {n(l25/12)} linhas por mês em média, todas de contas que treinaram.")
    p(f"- **2026 (jan a set):** {n(z26)} linhas com `minutos = 0` em {n(l26)} ({pc(z26, l26)}). O mês sem treino **aparece como linha com zero**. "
      f"As linhas por mês saltam de {n(a25.iloc[-1]['linhas'])} (dez/2025) para {n(a26.iloc[0]['linhas'])} (jan/2026), e o salto é quase todo de zeros: as linhas com `minutos > 0` ficam em {n(pos25)} por mês em 2025 e {n(pos26)} em 2026, enquanto as linhas totais passam de {n(l25/12)} para {n(l26/9)}.")
    p(f"- **Efeito na média do arquivo:** em 2025 ela é calculada só entre quem treinou (média de {d1(a25['media_arq'].mean())} min por mês); em 2026 entra o zero de quem não treinou e a média cai para "
      f"{d1(a26['media_arq'].mean())} min, e a mediana vai a {d1(a26['mediana_arq'].median())}. A queda vem da forma de registrar, não do comportamento: o denominador mudou.")
    p(f"- **Mesma população?** Entre as linhas com `minutos > 0` o denominador é o mesmo nos dois anos (quem treinou no mês): média de {d1(a25['media_pos'].mean())} min em 2025 e {d1(a26['media_pos'].mean())} min em 2026.\n")
    p("## 4. Qual média comparar entre 2025 e 2026\n")
    p("- **Pode comparar:** a média e a mediana só sobre as linhas com `minutos > 0` (quem treinou no mês), porque nos dois anos medem o mesmo grupo.")
    p("- **Não pode comparar:** a média e a mediana sobre o arquivo como está. Em 2025 o denominador exclui quem não treinou; em 2026 o inclui. A diferença é de registro.")
    p("- Para olhar o mês sem treino em 2025 seria preciso reconstruir as linhas ausentes (conta com assinatura vigente e sem linha = zero), o que o arquivo sozinho não permite.\n")
    p("## 5. Decisão proposta (formato do `decisoes.md`, não gravada)\n")
    p("| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |")
    p("|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|")
    p(f"| — | 09/11/2026 | uso_mensal.csv | mês sem treino é linha ausente em 2025 e linha com `minutos = 0` em 2026 ({n(z26)} zeros, {pc(z26, l26)} das linhas de 2026) | "
      f"marcar `linha_zero` (minutos = 0) na cópia tratada; comparar 2025 e 2026 só com `minutos > 0`; não criar linhas de zero para 2025 sem a base de assinaturas | "
      f"as médias do arquivo não são comparáveis entre os anos; remover os zeros de 2026 jogaria fora o dado de inatividade que só existe nesse ano | "
      f"{n(len(u))} linhas mantidas; {n(z26)} marcadas; {n(len(u) - z26)} com `minutos > 0` para a comparação |")
    p(f"\nContas de teste: {n(contas_teste_no_uso)} de {n(len(teste))} aparecem neste arquivo, então a exclusão não mudou nenhuma contagem.\n")

    estado = "inalterado" if sha256(USO, USUARIOS) == hash_antes else "ALTERADO"
    p(f"---\nConferência: arquivos brutos {estado}.")
    MD.write_text("\n".join(out), encoding="utf-8")

    # gráfico: duas faixas (arquivo e >0), média e mediana, mesma escala de y
    fundo, tinta, suave, azul, laranja = "#fcfcfb", "#0b0b0b", "#52514e", "#2a78d6", "#eb6834"
    fig, eixos = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True, facecolor=fundo)
    x = range(len(t))
    for ax, titulo, mcol, dcol in [(eixos[0], "Arquivo como está (inclui minutos = 0)", "media_arq", "mediana_arq"),
                                   (eixos[1], "Só linhas com minutos > 0", "media_pos", "mediana_pos")]:
        ax.set_facecolor(fundo)
        ax.plot(x, t[mcol], color=azul, lw=2, marker="o", ms=4, label="Média")
        ax.plot(x, t[dcol], color=laranja, lw=2, ls="--", marker="s", ms=4, label="Mediana")
        ax.axvline(11.5, color=suave, lw=0.8, ls=":")
        ax.set_ylim(0, 380)
        ax.text(11.8, 376, "2026: mês sem treino\nvira linha com zero", fontsize=8, color=suave, va="top")
        ax.set_title(titulo, fontsize=11, color=tinta, loc="left")
        ax.set_xticks(list(x)[::2])
        ax.set_xticklabels([m[2:] for m in t["mes"]][::2], fontsize=8, color=suave, rotation=45)
        ax.tick_params(colors=suave, labelsize=8)
        ax.grid(axis="y", color="#e6e5e0", lw=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color("#c9c8c2")
        ax.legend(frameon=False, fontsize=9, loc="center right" if mcol == "media_arq" else "lower right")
    eixos[0].set_ylabel("minutos por conta-mês", fontsize=9, color=suave)
    fig.suptitle("Uso mensal: média e mediana de minutos por mês (jan/2025 a set/2026)", fontsize=12, color=tinta, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(PNG, dpi=150, facecolor=fundo)

    print(f"brutos {estado} · soma por mês {'ok' if ok_total else 'ERRO'} · 21 meses {'ok' if ok_cobre else 'ERRO'}")
    print(f"escrito: {MD.relative_to(RAIZ)} · {PNG.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
