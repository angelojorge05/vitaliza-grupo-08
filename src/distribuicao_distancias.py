"""Análise 9 · Distribuição de distancia_km em dados/brutos/atividades.parquet (Colaborador 4).

Forma da distância dos treinos (tabela de frequências e histograma em classes
de 5 km), quartis, e extremos marcados por duas regras — Q3 + 1,5×IQR e |z| > 3 —
sem apagar nada: a regra marca; o grupo decide.

Só leitura (hash SHA-256 antes e depois). Saídas em saidas/:
- distribuicao_distancias.md (tabelas)
- distribuicao_distancias.png (histograma)

Roteiro: docs/analises_por_colaborador/colaborador_4.md, análise 9.
"""

import hashlib
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "dados" / "brutos" / "atividades.parquet"
SAIDA_MD = RAIZ / "saidas" / "distribuicao_distancias.md"
SAIDA_PNG = RAIZ / "saidas" / "distribuicao_distancias.png"
MAPA = {"run": "corrida", "walk": "caminhada", "ride": "pedal", "strength": "forca"}


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def fmt(n) -> str:
    return f"{n:,}".replace(",", ".")


def br(x, nd=2) -> str:
    return f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main() -> None:
    hash_antes = sha256(ARQUIVO)
    df = pd.read_parquet(ARQUIVO, columns=["tipo", "distancia_km"])
    d = df.dropna(subset=["distancia_km"]).copy()
    d["tipo_canon"] = d["tipo"].map(lambda t: MAPA.get(t, t))
    s = d["distancia_km"]
    n = len(s)
    print(f"treinos com distancia_km preenchida: {fmt(n)} (de {fmt(len(df))})")

    # --- tabela de frequências: classes de 5 km, última 60+ ---
    limites = list(range(0, 61, 5)) + [float("inf")]
    rotulos = [f"{a}–{a+5}" for a in range(0, 60, 5)] + ["60+"]
    classes = pd.cut(s, bins=limites, labels=rotulos, right=False, include_lowest=True)
    freq = classes.value_counts().reindex(rotulos)
    tab_freq = pd.DataFrame({"classe (km)": rotulos, "treinos": freq.values,
                             "%": [100 * v / n for v in freq.values]})
    print("\n=== tabela de frequências (classes de 5 km) ===")
    print(tab_freq.to_string(index=False, formatters={"treinos": fmt, "%": lambda p: f"{p:.1f}%"}))

    # --- quartis ---
    q1, med, q3 = s.quantile([0.25, 0.5, 0.75])
    iqr = q3 - q1
    print(f"\nQ1={br(q1)} km · mediana={br(med)} · Q3={br(q3)} · IQR={br(iqr)}")

    # --- regra 1: Q3 + 1,5×IQR ---
    lim_iqr = q3 + 1.5 * iqr
    m_iqr = s > lim_iqr
    por_tipo_iqr = d.loc[m_iqr, "tipo_canon"].value_counts()
    print(f"\n=== extremos por Q3 + 1,5×IQR (> {br(lim_iqr)} km) ===")
    print(f"marcados: {fmt(int(m_iqr.sum()))}")
    print(por_tipo_iqr.to_string())

    # --- regra 2: |z| > 3 ---
    z = (s - s.mean()) / s.std(ddof=1)
    m_z = z.abs() > 3
    lim_z = s.mean() + 3 * s.std(ddof=1)
    por_tipo_z = d.loc[m_z, "tipo_canon"].value_counts()
    print(f"\n=== extremos por |z| > 3 (> {br(lim_z)} km; média {br(s.mean())}, dp {br(s.std(ddof=1))}) ===")
    print(f"marcados: {fmt(int(m_z.sum()))}")
    print(por_tipo_z.to_string())

    # --- histograma ---
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(rotulos, freq.values, color="#4C78A8", edgecolor="white")
    ax.set_title("Distância dos treinos com GPS — classes de 5 km (n = %s)" % fmt(n))
    ax.set_xlabel("distância (km)")
    ax.set_ylabel("treinos")
    ax.axvline(x=lim_iqr / 5 - 0.5, color="#E45756", linestyle="--", linewidth=1.2,
               label=f"Q3 + 1,5×IQR = {br(lim_iqr)} km")
    for i, v in enumerate(freq.values):
        ax.text(i, v, f"{100 * v / n:.1f}%", ha="center", va="bottom", fontsize=8)
    ax.legend()
    fig.tight_layout()
    fig.savefig(SAIDA_PNG, dpi=150)
    print(f"\nhistograma: {SAIDA_PNG.relative_to(RAIZ)}")

    # --- relatório md ---
    linhas = [
        "# Distribuição das distâncias (análise 9 · Colaborador 4)",
        "",
        f"Gerado por `src/distribuicao_distancias.py` a partir de `dados/brutos/atividades.parquet` "
        f"(só leitura; hash `{hash_antes[:16]}…` conferido antes e depois). Nada foi removido: "
        "as duas regras abaixo **marcam** extremos; a decisão é do grupo (`decisoes.md`).",
        "",
        f"- Treinos com `distancia_km` preenchida: **{fmt(n)}** de {fmt(len(df))} "
        "(os demais não tinham GPS — ausência, não erro).",
        f"- Quartis: Q1 **{br(q1)}** km · mediana **{br(med)}** · Q3 **{br(q3)}** · IQR **{br(iqr)}**.",
        "",
        "## Tabela de frequências (classes de 5 km)",
        "",
        "| classe (km) | treinos | % |",
        "|---|---:|---:|",
    ]
    for r in tab_freq.itertuples():
        linhas.append(f"| {r[1]} | {fmt(r[2])} | {r[3]:.1f}% |".replace(".", ","))
    linhas += [
        "",
        "## Extremos marcados (nada removido)",
        "",
        f"**Regra 1 — Q3 + 1,5×IQR (> {br(lim_iqr)} km):** {fmt(int(m_iqr.sum()))} treinos. Por tipo "
        "(nomes em inglês somados ao equivalente em português, mapa da análise 4): "
        + ", ".join(f"{t} {fmt(v)}" for t, v in por_tipo_iqr.items()) + ".",
        "",
        f"**Regra 2 — |z| > 3 (> {br(lim_z)} km):** {fmt(int(m_z.sum()))} treinos. Por tipo: "
        + ", ".join(f"{t} {fmt(v)}" for t, v in por_tipo_z.items()) + ".",
        "",
        "A regra do IQR marca treinos longos porém plausíveis (pedais de 20–60 km); a regra do z "
        "marca só o fisicamente impossível (centenas a milhares de km). Proposta para o `decisoes.md`: "
        "**marcar** pelos dois critérios e excluir dos agregados de engajamento apenas os impossíveis "
        "(>200 km, análise 3), mantendo o registro bruto intacto.",
        "",
        f"![histograma](distribuicao_distancias.png)",
    ]
    SAIDA_MD.write_text("\n".join(linhas), encoding="utf-8")
    print(f"relatório: {SAIDA_MD.relative_to(RAIZ)}")

    estado = "inalterado" if sha256(ARQUIVO) == hash_antes else "ALTERADO"
    print(f"\natividades.parquet {estado}")


if __name__ == "__main__":
    main()
