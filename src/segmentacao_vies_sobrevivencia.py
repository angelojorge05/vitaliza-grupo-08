"""Viés de sobrevivência na segmentação de referência (decisões 45 a 47): ela só usa os ativos de 30/09/2026.

Passos (plano aprovado em 10/11/2026):
0. reproduzir o modelo de referência (10 variáveis, k = 4) e conferir com segmentos_ampliada_30set.parquet;
1. classificar os ativos de 30/04, 31/05 e 30/06 pelos centros de 30/09 (proporções e transições);
2. em que grupo estava quem saiu (rótulo de 60 dias e perdidos entre 30/06 e 30/09; reponderação);
3. K-means com os quatro cortes empilhados (ARI com a referência, bootstrap por assinante, k = 2..6).
Só lê arquivos; a segmentação de referência não muda.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import segmentacao_ampliada as sa  # noqa: E402
import segmentacao_kmeans as sk  # noqa: E402

n, g, tabela, sha = sk.n, sk.g, sk.tabela, sk.sha
PROC, SAIDAS, RAIZ = sk.PROC, sk.SAIDAS, sk.RAIZ
MD = SAIDAS / "segmentacao_vies_sobrevivencia.md"
PNG = SAIDAS / "segmentacao_vies_sobrevivencia.png"
REF = PROC / "segmentos_ampliada_30set.parquet"
NUM_F = ["minutos_por_treino_90d", "recencia_dias", "tendencia", "n_modalidades_90d", "pct_relogio_90d", "sessoes_app_3m",
         "n_seguidores", "n_posts_90d", "dias_desde_cadastro", "dias_semana"]  # decisão 46
CAT_F: list[str] = []
K = 4
CORTES = ["2026-04-30", "2026-05-31", "2026-06-30", "2026-09-30"]
ROT = {c: pd.Timestamp(c).strftime("%d/%m") for c in CORTES}
CORES = {1: "#2a78d6", 2: "#eb6834", 3: "#1baf7a", 4: "#eda100"}


def ic(p: float, total: int) -> str:
    e = 1.96 * np.sqrt(p * (1 - p) / total)
    return f"{g(100 * p)} ({g(100 * (p - e))}–{g(100 * (p + e))})"


def main() -> None:
    entradas = [sk.MASTER, REF, sa.USUARIOS, sk.TREINOS_V2] + [PROC / f"base_assinantes_{c}.parquet" for c in CORTES[:3]]
    hashes = {p: sha(p) for p in entradas}
    log: list[list[str]] = []
    m = pd.read_parquet(sk.MASTER)
    sexo, _ = sa.imputar_sexo(m, [])
    cad = pd.to_datetime(pd.read_csv(sa.USUARIOS, dtype=str, usecols=["user_id", "data_cadastro"]).set_index("user_id")["data_cadastro"])
    t = pd.read_parquet(sk.TREINOS_V2, columns=["user_id", "inicio", "tipo"])

    # ---------------- passo 0: modelo de referência
    a9 = m[m["ativo_no_corte"]].copy()
    a9 = sa.montar(a9, pd.Timestamp(CORTES[3]), t, sexo, cad, None)
    tab_freq, _ = sa.calibrar_frequencia(a9)
    a9["dias_semana"] = a9["dias_semana_declarado"].fillna(sa.aplicar_frequencia(a9["freq_obs_semana"], tab_freq))
    log.append(["ativos em 30/09 (base master)", n(len(m)), n(len(a9)), "`ativo_no_corte`"])
    prep, km = sa.ajustar(a9[NUM_F], NUM_F, CAT_F, K)
    ordem = np.argsort(-np.bincount(km.labels_))
    renome = {int(o): i + 1 for i, o in enumerate(ordem)}
    a9["grupo"] = [renome[int(c)] for c in km.labels_]
    ref = pd.read_parquet(REF)
    chk = a9[["user_id", "grupo"]].merge(ref, on="user_id", how="inner", validate="1:1", suffixes=("", "_ref"))
    ari0 = adjusted_rand_score(chk["grupo_ref"], chk["grupo"])
    iguais = int((chk["grupo"] == chk["grupo_ref"]).sum())
    print(f"[0] reprodução: {n(len(chk))} contas · ARI {ari0:.4f} · grupo idêntico em {n(iguais)}")
    assert iguais == len(chk) == len(ref), "o modelo de referência não foi reproduzido"
    pers = ref.drop_duplicates("grupo").set_index("grupo")["persona"].to_dict()

    def classificar(df):
        return np.array([renome[int(c)] for c in km.predict(prep.transform(df[NUM_F]))])

    # ---------------- passo 1: grupos em cada corte
    bases = {}
    for c in CORTES[:3]:
        b = pd.read_parquet(PROC / f"base_assinantes_{c}.parquet")
        n0 = len(b)
        b = sa.montar(b, pd.Timestamp(c), t, sexo, cad, tab_freq)
        assert len(b) == n0 and b["user_id"].is_unique
        b["grupo"] = classificar(b)
        b["corte"] = c
        bases[c] = b
        log.append([f"ativos em {ROT[c]} (base_assinantes)", n(n0), n(len(b)), "montada no próprio corte; junções 1:1"])
    a9["corte"] = CORTES[3]
    bases[CORTES[3]] = a9
    prop = pd.DataFrame({c: bases[c]["grupo"].value_counts(normalize=True).sort_index() for c in CORTES})
    tot = {c: len(bases[c]) for c in CORTES}
    dif_max = float((prop[CORTES[:3]].sub(prop[CORTES[3]], axis=0)).abs().max().max())
    print("[1] proporções por corte:\n" + (100 * prop).round(1).to_string() + f"\n    maior diferença contra 30/09: {100 * dif_max:.1f} p.p.")
    anual = pd.DataFrame({c: bases[c].assign(anual=bases[c]["plano_atual"].eq("anual")).groupby("grupo")["anual"].mean() for c in CORTES})
    trans = []
    for c0, c1 in zip(CORTES[:-1], CORTES[1:]):
        j = bases[c0][["user_id", "grupo"]].merge(bases[c1][["user_id", "grupo"]], on="user_id", how="inner", suffixes=("_0", "_1"), validate="1:1")
        mt = pd.crosstab(j["grupo_0"], j["grupo_1"], normalize="index")
        trans.append((c0, c1, len(j), float((j["grupo_0"] == j["grupo_1"]).mean()), mt))
        log.append([f"ativos em {ROT[c0]} e em {ROT[c1]}", f"{n(len(bases[c0]))} / {n(len(bases[c1]))}", n(len(j)), "junção interna por `user_id`"])
        print(f"[1] {c0} → {c1}: {len(j)} nos dois · ficam no mesmo grupo {100 * trans[-1][3]:.1f}%")

    # ---------------- passo 2: quem saiu
    sai_rot = []
    for c in CORTES[:3]:
        b = bases[c]
        for gr in range(1, K + 1):
            s = b[b["grupo"] == gr]
            sai_rot.append(dict(corte=c, grupo=gr, contas=len(s), saiu=s["saiu_60d"].mean(),
                                pct_entre_saidas=(b.loc[b["saiu_60d"], "grupo"] == gr).mean(),
                                pct_entre_ficam=(b.loc[~b["saiu_60d"], "grupo"] == gr).mean()))
    sai_rot = pd.DataFrame(sai_rot)
    b6 = bases["2026-06-30"]
    ativos9 = set(a9["user_id"])
    b6["perdido"] = ~b6["user_id"].isin(ativos9)
    perd = b6[b6["perdido"]]
    log.append(["ativos em 30/06 que não estão ativos em 30/09 (perdidos)", n(len(b6)), n(len(perd)), "`user_id` fora dos ativos de 30/09"])
    comp_perd = pd.DataFrame({"perdidos": perd["grupo"].value_counts(normalize=True), "continuaram": b6.loc[~b6["perdido"], "grupo"].value_counts(normalize=True),
                              "perda_no_grupo": b6.groupby("grupo")["perdido"].mean()}).sort_index()
    cont9 = a9["grupo"].value_counts().sort_index()
    repond = (cont9 + perd["grupo"].value_counts().reindex(cont9.index, fill_value=0)) / (len(a9) + len(perd))
    print("[2] perdidos 30/06→30/09 por grupo:\n" + (100 * comp_perd).round(1).to_string())
    print("[2] 30/09 reponderado: " + ", ".join(f"{gr}: {100 * v:.1f}%" for gr, v in repond.items()))

    # ---------------- passo 3: empilhado
    E = pd.concat([bases[c][["user_id", "corte", "grupo", "plano_atual", "recencia_dias"] + NUM_F] for c in CORTES], ignore_index=True)
    log.append(["cortes empilhados", " + ".join(n(tot[c]) for c in CORTES), n(len(E)), f"{n(E['user_id'].nunique())} assinantes distintos"])
    prep_e, km_e = sa.ajustar(E[NUM_F], NUM_F, CAT_F, K)
    E["grupo_emp"] = km_e.labels_
    so9 = E["corte"] == CORTES[3]
    ari_9 = adjusted_rand_score(E.loc[so9, "grupo"], E.loc[so9, "grupo_emp"])
    ari_tudo = adjusted_rand_score(E["grupo"], E["grupo_emp"])
    cruz_e = pd.crosstab(E["grupo"].map(pers), E["grupo_emp"])
    print(f"[3] ARI empilhado × referência: 30/09 {ari_9:.3f} · todas as linhas {ari_tudo:.3f}")
    rng = np.random.default_rng(sa.SEMENTE)
    usuarios = E["user_id"].unique()
    pos = E.groupby("user_id").indices
    ari_boot = []
    for b in range(20):
        amostra = rng.choice(usuarios, size=len(usuarios), replace=True)
        idx = np.concatenate([pos[u] for u in amostra])
        p_b, km_b = sa.ajustar(E[NUM_F].iloc[idx], NUM_F, CAT_F, K, semente=sa.SEMENTE + 300 + b, n_init=5)
        ari_boot.append(adjusted_rand_score(E["grupo_emp"], km_b.predict(p_b.transform(E[NUM_F]))))
    print(f"[3] bootstrap por assinante: ARI {np.mean(ari_boot):.3f} (mín {np.min(ari_boot):.3f})")
    amostra = rng.choice(len(E), size=6000, replace=False)
    ks, grupos_k = [], []
    for k in range(2, 7):
        p_k, km_k = sa.ajustar(E[NUM_F], NUM_F, CAT_F, k, n_init=10)
        Z, lab = p_k.transform(E[NUM_F]), km_k.labels_
        ks.append(dict(k=k, silhueta=silhouette_score(Z[amostra], lab[amostra]), calinski=calinski_harabasz_score(Z, lab),
                       davies=davies_bouldin_score(Z, lab), ari_ref=adjusted_rand_score(E["grupo"], lab)))
        El = E.assign(l=lab, mensal=E["plano_atual"].eq("mensal"))
        d = El.groupby("l").agg(contas=("user_id", "size"), mensal=("mensal", "mean"), recencia=("recencia_dias", "median"))
        dist = pd.crosstab(El["l"], El["grupo"], normalize="index")
        d["persona"] = dist.idxmax(axis=1).map(pers)
        d["pct_persona"] = dist.max(axis=1)
        d["k"] = k
        grupos_k.append(d.sort_values("contas", ascending=False))
        print(f"[3] k={k}: silhueta {ks[-1]['silhueta']:.3f} · ARI com a referência {ks[-1]['ari_ref']:.3f} · " +
              "; ".join(f"{n(r.contas)} ({100 * r.mensal:.0f}% mensal, rec {r.recencia:.0f}, ~{r.persona})" for r in d.sort_values('contas', ascending=False).itertuples()))
    ks = pd.DataFrame(ks)

    # ---------------- gráfico
    fundo, tinta, suave = "#fcfcfb", "#0b0b0b", "#52514e"
    fig, eixos = plt.subplots(1, 2, figsize=(12.5, 4.4), facecolor=fundo)
    ax = eixos[0]
    x = np.arange(len(CORTES))
    for gr in range(1, K + 1):
        ax.plot(x, 100 * prop.loc[gr].values, color=CORES[gr], lw=2, marker="o", ms=6, label=f"{gr} {pers[gr]}")
        ax.text(x[-1] + 0.08, 100 * prop.loc[gr].iloc[-1], f"{g(100 * prop.loc[gr].iloc[-1])}%", va="center", fontsize=8, color=tinta)
    ax.set_xticks(x)
    ax.set_xticklabels([ROT[c] for c in CORTES])
    ax.set_xlim(-0.2, len(CORTES) - 0.5)
    ax.set_ylabel("% dos ativos no corte", fontsize=9, color=suave)
    ax.set_title("Proporção de cada grupo por corte (centros de 30/09)", fontsize=10, color=tinta, loc="left")
    ax.legend(fontsize=7.5, frameon=False, loc="upper center", ncol=2, bbox_to_anchor=(0.5, -0.1))
    ax = eixos[1]
    largura = 0.38
    xs = np.arange(K)
    ax.bar(xs - largura / 2 - 0.01, 100 * comp_perd["continuaram"].values, largura, color="#b5b3ad", label="continuaram até 30/09")
    ax.bar(xs + largura / 2 + 0.01, 100 * comp_perd["perdidos"].values, largura, color=[CORES[gr] for gr in comp_perd.index], label="perdidos até 30/09 (cor do grupo)")
    for i, gr in enumerate(comp_perd.index):
        ax.text(xs[i] + largura / 2, 100 * comp_perd.loc[gr, "perdidos"] + 0.8, f"{g(100 * comp_perd.loc[gr, 'perdidos'])}%", ha="center", fontsize=8, color=tinta)
        ax.text(xs[i] - largura / 2, 100 * comp_perd.loc[gr, "continuaram"] + 0.8, f"{g(100 * comp_perd.loc[gr, 'continuaram'])}%", ha="center", fontsize=8, color=suave)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{gr} {pers[gr]}" for gr in comp_perd.index], fontsize=7.5)
    ax.set_ylabel("% do grupo entre os ativos de 30/06", fontsize=9, color=suave)
    ax.set_title("Grupo em 30/06: quem continuou × quem foi perdido até 30/09", fontsize=10, color=tinta, loc="left")
    ax.legend(fontsize=7.5, frameon=False)
    for ax in eixos:
        ax.set_facecolor(fundo)
        ax.tick_params(colors=suave, labelsize=8)
        ax.grid(axis="y", color="#e6e5e0", lw=0.6)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"):
            ax.spines[sp].set_color("#c9c8c2")
    fig.tight_layout()
    fig.savefig(PNG, dpi=150, facecolor=fundo)

    # ---------------- relatório
    L = ["# Viés de sobrevivência na segmentação (ativos em 30/09/2026)\n",
         "Gerado por `src/segmentacao_vies_sobrevivencia.py`. Só leitura (SHA-256 das entradas conferido antes e depois). "
         "A segmentação de referência (`segmentos_ampliada_30set.parquet`, decisões 45 a 47) não muda.\n",
         "**Pergunta:** a segmentação usa só quem estava ativo em 30/09. Quem saiu antes não está nela. Isso distorce os grupos?\n",
         "## 0. Contas e reprodução do modelo\n",
         tabela(pd.DataFrame(log, columns=["passo", "antes", "depois", "observação"])) + "\n",
         f"Modelo de referência refeito (10 variáveis da decisão 46, k = 4, mesma semente): grupo idêntico em {n(iguais)} de {n(len(ref))} contas (ARI {g(ari0, 3)}). "
         "Os outros cortes foram montados no próprio corte (treinos, cadastro e 90 dias até a data) e classificados pelos centros de 30/09.\n",
         "## 1. Os grupos em cada corte\n",
         "% dos ativos (intervalo de 95%):\n"]
    L.append(tabela(pd.DataFrame({"grupo": [f"{gr} {pers[gr]}" for gr in prop.index],
                                  **{f"{ROT[c]} ({n(tot[c])})": [ic(prop.loc[gr, c], tot[c]) for gr in prop.index] for c in CORTES}})) + "\n")
    L.append(f"Maior diferença contra 30/09: **{g(100 * dif_max)} p.p.** (critério do plano: até 2 p.p. = a foto de setembro é típica).\n")
    L.append("% de anuais em cada grupo e corte:\n")
    L.append(tabela(pd.DataFrame({"grupo": [f"{gr} {pers[gr]}" for gr in anual.index], **{ROT[c]: (100 * anual[c]).map(g).values for c in CORTES}})) + "\n")
    L.append("Transições entre cortes (quem estava ativo nos dois; linhas = grupo no corte anterior, % que vai para cada grupo):\n")
    for c0, c1, q, fica, mt in trans:
        L.append(f"**{ROT[c0]} → {ROT[c1]}** ({n(q)} assinantes; {g(100 * fica)}% ficam no mesmo grupo):\n")
        L.append(tabela((100 * mt).round(1).rename(index=lambda i: f"{i} {pers[i]}").reset_index().rename(columns={"grupo_0": "de \\ para"}).astype(str)) + "\n")
    L.append("## 2. Em que grupo estava quem saiu\n")
    L.append("### 2.1 Rótulo de 60 dias em cada corte\n")
    L.append(tabela(pd.DataFrame({"corte": sai_rot["corte"].map(ROT), "grupo": sai_rot["grupo"].map(lambda gr: f"{gr} {pers[gr]}"),
                                  "contas": sai_rot["contas"].map(n), "saiu em 60 dias": (100 * sai_rot["saiu"]).map(lambda v: g(v) + "%"),
                                  "% entre os que saíram": (100 * sai_rot["pct_entre_saidas"]).map(g),
                                  "% entre os que ficaram": (100 * sai_rot["pct_entre_ficam"]).map(g)})) + "\n")
    L.append("A janela de 60 dias de 30/06 passa pela campanha de 10/08; as de 30/04 e 31/05, não.\n")
    L.append("### 2.2 Perdidos entre 30/06 e 30/09\n")
    L.append(f"{n(len(perd))} dos {n(len(b6))} ativos de 30/06 não estão ativos em 30/09 ({g(100 * len(perd) / len(b6))}%).\n")
    L.append(tabela(pd.DataFrame({"grupo em 30/06": [f"{gr} {pers[gr]}" for gr in comp_perd.index],
                                  "% entre os perdidos": (100 * comp_perd["perdidos"]).map(g).values,
                                  "% entre os que continuaram": (100 * comp_perd["continuaram"]).map(g).values,
                                  "% do grupo que foi perdido": (100 * comp_perd["perda_no_grupo"]).map(g).values})) + "\n")
    L.append("**Reponderação:** proporções de 30/09 se os perdidos voltassem para o grupo que tinham em 30/06.\n")
    L.append(tabela(pd.DataFrame({"grupo": [f"{gr} {pers[gr]}" for gr in repond.index], "30/09 (observado)": (100 * prop[CORTES[3]]).map(g).values,
                                  "30/09 reponderado": (100 * repond).map(g).values,
                                  "diferença (p.p.)": (100 * (repond - prop[CORTES[3]])).map(lambda v: f"{v:+.1f}".replace(".", ",")).values})) + "\n")
    L.append("![viés](segmentacao_vies_sobrevivencia.png)\n")
    L.append("## 3. K-means com os quatro cortes empilhados\n")
    L.append(f"{n(len(E))} linhas (uma por assinante e corte; {n(E['user_id'].nunique())} assinantes), mesmas 10 variáveis, mesmo pré-processamento, k = 4.\n")
    L.append(tabela(pd.DataFrame([
        ["ARI empilhado × referência, linhas de 30/09", g(ari_9, 3)],
        ["ARI empilhado × referência, todas as linhas", g(ari_tudo, 3)],
        ["bootstrap por assinante (20 reamostragens): ARI médio", g(np.mean(ari_boot), 3)],
        ["bootstrap por assinante: pior ARI", g(np.min(ari_boot), 3)],
    ], columns=["medida", "valor"])) + "\n")
    L.append("Critério do plano: ARI ≥ 0,9 = os grupos não dependem de terem sobrevivido até setembro. Cruzamento (linhas = persona de referência; colunas = grupo do empilhado):\n")
    L.append(tabela(cruz_e.reset_index().astype(str)) + "\n")
    L.append("Outros k no empilhado (há algum grupo que a foto de 30/09 perde?):\n")
    L.append(tabela(pd.DataFrame({"k": ks["k"], "silhueta": ks["silhueta"].map(lambda v: g(v, 3)), "Calinski-Harabasz": ks["calinski"].map(lambda v: g(v, 0)),
                                  "Davies-Bouldin": ks["davies"].map(lambda v: g(v, 3)), "ARI com a referência": ks["ari_ref"].map(lambda v: g(v, 3))})) + "\n")
    gk = pd.concat(grupos_k)
    L.append(tabela(pd.DataFrame({"k": gk["k"], "contas": gk["contas"].map(n), "% mensal": (100 * gk["mensal"]).map(g),
                                  "recência (mediana)": gk["recencia"].map(lambda v: g(v, 0)),
                                  "persona de referência mais comum": [f"{p} ({g(100 * q)}%)" for p, q in zip(gk["persona"], gk["pct_persona"])]})) + "\n")
    L.append("## 4. Leitura\n")
    esf = cruz_e.loc[pers[3]]
    L.append(f"- **O viés existe, mas é pequeno e concentrado no grupo Esfriando.** Entre os perdidos de 30/06 a 30/09, {g(100 * comp_perd.loc[3, 'perdidos'])}% eram Esfriando "
             f"(contra {g(100 * comp_perd.loc[3, 'continuaram'])}% entre os que continuaram) e {g(100 * comp_perd.loc[4, 'perdidos'])}% Parado (contra {g(100 * comp_perd.loc[4, 'continuaram'])}%). "
             f"Devolvendo os perdidos, o Esfriando de 30/09 passaria de {g(100 * prop.loc[3, CORTES[3]])}% para {g(100 * repond.loc[3])}%: a foto de setembro subestima um pouco quem esfria, "
             "porque parte já saiu.")
    L.append(f"- **As proporções quase não mudam entre cortes**, mas o Esfriando cresce de {g(100 * prop.loc[3, CORTES[0]])}% (30/04) para {g(100 * prop.loc[3, CORTES[3]])}% (30/09), "
             f"e a diferença máxima ({g(100 * dif_max)} p.p.) passa um pouco do critério de 2 p.p. Dentro do Esfriando a parcela de anuais sobe de {g(100 * anual.loc[3, CORTES[0]])}% para "
             f"{g(100 * anual.loc[3, CORTES[3]])}%: o mensal que esfria sai, o anual que esfria fica. É o efeito do plano descrito na pergunta.")
    L.append(f"- **O Parado é anual em todos os cortes** ({g(100 * anual.loc[4].min())}% a {g(100 * anual.loc[4].max())}%). Nenhum k do empilhado (2 a 6) mostra um \"mensal parado\": "
             "o mensal que para de treinar sai antes de chegar a 90 dias sem treino. O grupo depende da regra do plano, não só do comportamento.")
    L.append(f"- **No empilhado, os grupos centrais se repetem** (ARI {g(ari_tudo, 3)}, um pouco abaixo do critério de 0,9). A diferença está quase toda no Esfriando: "
             f"{n(esf.max())} de {n(esf.sum())} linhas de Esfriando ({g(100 * esf.max() / esf.sum())}%) caem no mesmo grupo; o resto vai para os engajados. "
             "Engajado no app, Engajado com relógio e Parado coincidem em mais de 98%. A fronteira do Esfriando é a menos firme.")
    L.append(f"- **Quem sai, sai mais do Esfriando em todos os cortes** ({g(100 * sai_rot.query('grupo == 3')['saiu'].min())}% a {g(100 * sai_rot.query('grupo == 3')['saiu'].max())}% em 60 dias, "
             f"contra {g(100 * sai_rot.query('grupo in [1, 2]')['saiu'].min())}% a {g(100 * sai_rot.query('grupo in [1, 2]')['saiu'].max())}% dos engajados). O Esfriando é o grupo de maior risco em todos os cortes; os dois engajados ficam sempre abaixo de 12% e trocam de posição entre si.\n")
    L.append("**Consequências:**\n")
    L.append("1. Para escolher quem contatar (objetivo 6), a segmentação de 30/09 serve: só é possível agir sobre quem está ativo, e o Esfriando é o de maior risco em todos os cortes.")
    L.append(f"2. Para descrever a base, dizer que \"{g(100 * prop.loc[3, CORTES[3]])}% esfriam\" subestima: o valor reponderado é {g(100 * repond.loc[3])}%, e ao longo do ano mais gente passa pelo Esfriando do que a foto mostra.")
    L.append("3. Para explicar a alta do churn em 2026 (objetivo 2), não usar só os grupos de 30/09: usar os grupos de cada corte (seção 1), que incluem quem saiu depois.")
    L.append("4. Para o modelo de previsão, usar o grupo calculado em cada corte, nunca o de 30/09, para não carregar a sobrevivência para o treino.\n")
    L.append("---\nConferências: " + "; ".join(f"`{p.name}` {'inalterado' if sha(p) == h else 'ALTERADO'}" for p, h in hashes.items()) + ".")
    MD.write_text("\n".join(L), encoding="utf-8")
    print(f"escrito: {MD.relative_to(RAIZ)} · {PNG.relative_to(RAIZ)} · " + ", ".join("ok" if sha(p) == h else f"{p.name} ALTERADO" for p, h in hashes.items()))


if __name__ == "__main__":
    main()
