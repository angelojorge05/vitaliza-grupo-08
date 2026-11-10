"""Segmentação K-means dos assinantes ativos em 30/09/2026 (objetivo 3 do case), sem usar a saída.

Uso:
  python src/segmentacao_kmeans.py            -> só a escolha de k (k = 2..10)
  python src/segmentacao_kmeans.py --k 5      -> modelo final, validação cruzada e perfil

Decisões aprovadas pelo usuário (10/11/2026):
- grupos formados só com contas completas (perfil e onboarding declarados): 14.753 -> 11.032;
- só variáveis de comportamento marcadas `agrupamento` na base master (perfil e pagamentos fora);
- a taxa de saída em 60 dias por grupo é mostrada DEPOIS, no corte de 30/06 (só descreve).
Pré-processamento ajustado só nos dados de treino de cada ajuste: teto no p99 -> log1p nas contagens
-> padronização z. A base master não é alterada. Só lê arquivos (dados/processados/ e brutos).
"""

import argparse
import hashlib
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score,
                             silhouette_score)
from sklearn.model_selection import KFold

RAIZ = Path(__file__).resolve().parent.parent
PROC = RAIZ / "dados" / "processados"
SAIDAS = RAIZ / "saidas"
MASTER = PROC / "base_master.parquet"
BASE_30JUN = PROC / "base_assinantes_2026-06-30.parquet"
TREINOS_V2 = PROC / "atividades_limpa_v2.parquet"
MD = SAIDAS / "segmentacao_kmeans.md"
SEMENTE = 42
VARS = ["treinos_90d", "minutos_por_treino_90d", "recencia_dias", "tendencia", "pct_ar_livre", "n_modalidades_90d",
        "pct_relogio_90d", "sessoes_app_3m", "n_seguidores", "n_posts_90d"]
LOG = ["treinos_90d", "minutos_por_treino_90d", "tendencia", "sessoes_app_3m", "n_seguidores", "n_posts_90d"]
RETIRADAS = {"minutos_90d": "correlação de Spearman 0,97 com `treinos_90d` (substituída por `minutos_por_treino_90d`)",
             "n_tickets_90d": "quase constante (média 0,04, máximo 2): formaria um grupo só de quem abriu ticket; vai para o perfil"}
COMPLETUDE = ["idade ausente ou inválida", "sexo não informado", "nível não informado", "dias por semana não informado"]
AR_LIVRE = ["corrida", "caminhada", "pedal"]
# nomes dados depois de ler o perfil do modelo com k = 4 (grupo 1 = o maior)
PERSONAS = {1: "Engajado no app", 2: "Engajado com relógio", 3: "Esfriando", 4: "Parado (anual dormente)"}


def n(x) -> str:
    return f"{int(x):,}".replace(",", ".")


def g(x, d=1) -> str:
    return "—" if pd.isna(x) else f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tabela(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    return "\n".join([cab, sep, *("| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False))])


def sha(c: Path) -> str:
    return hashlib.sha256(c.read_bytes()).hexdigest()


class Preparo:
    """Teto no p99, log1p nas contagens e padronização z, ajustados só no treino."""

    def fit(self, X: pd.DataFrame) -> "Preparo":
        self.teto = X.quantile(0.99)
        Z = self._base(X)
        self.media, self.dp = Z.mean(), Z.std(ddof=0).replace(0, 1)
        return self

    def _base(self, X: pd.DataFrame) -> pd.DataFrame:
        Z = X.clip(upper=self.teto, axis=1).copy()
        for c in LOG:
            Z[c] = np.log1p(Z[c])
        return Z

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        return ((self._base(X) - self.media) / self.dp).to_numpy()


def ajustar(X: pd.DataFrame, k: int, semente: int = SEMENTE, n_init: int = 20):
    prep = Preparo().fit(X)
    km = KMeans(n_clusters=k, n_init=n_init, random_state=semente).fit(prep.transform(X))
    return prep, km


def prever(prep: Preparo, km: KMeans, X: pd.DataFrame) -> np.ndarray:
    return km.predict(prep.transform(X))


def jaccard_por_grupo(ref: np.ndarray, novo: np.ndarray, k: int) -> np.ndarray:
    """Casa os grupos novos com os de referência (Hungarian) e devolve o Jaccard de cada grupo de referência."""
    inter = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            inter[i, j] = np.sum((ref == i) & (novo == j))
    tam_r, tam_n = np.bincount(ref, minlength=k), np.bincount(novo, minlength=k)
    jac = inter / (tam_r[:, None] + tam_n[None, :] - inter + 1e-9)
    lin, col = linear_sum_assignment(-jac)
    out = np.zeros(k)
    out[lin] = jac[lin, col]
    return out


def carregar() -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    m = pd.read_parquet(MASTER)
    log = []
    log.append(f"| base_master | {n(len(m))} | {n(len(m))} | uma linha por conta |")
    a = m[m["ativo_no_corte"]].copy()
    log.append(f"| ativos no corte (sem teste) | {n(len(m))} | {n(len(a))} | `ativo_no_corte` |")
    a["minutos_por_treino_90d"] = np.where(a["treinos_90d"] > 0, a["minutos_90d"] / a["treinos_90d"].where(a["treinos_90d"] > 0), 0.0)
    falta = {
        COMPLETUDE[0]: a["idade"].isna(), COMPLETUDE[1]: a["sexo"].eq("nao_informado"),
        COMPLETUDE[2]: a["nivel_nao_informado"], COMPLETUDE[3]: a["dias_por_semana_nao_informado"],
    }
    incompleto = pd.concat(falta, axis=1).any(axis=1)
    a["completo"] = ~incompleto
    for nome, s in falta.items():
        log.append(f"| ↳ com {nome} | {n(len(a))} | {n(int(s.sum()))} | marca |")
    log.append(f"| contas completas (formam os grupos) | {n(len(a))} | {n(int(a['completo'].sum()))} | {n(int(incompleto.sum()))} incompletas ficam fora do ajuste |")
    return m, a, log


def escolha_k(X: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    rng = np.random.default_rng(SEMENTE)
    amostra = rng.choice(len(X), size=min(5000, len(X)), replace=False)
    for k in range(2, 11):
        prep, km = ajustar(X, k)
        Z = prep.transform(X)
        lab = km.labels_
        sil = silhouette_score(Z[amostra], lab[amostra])
        aris = []
        for b in range(10):
            idx = rng.choice(len(X), size=len(X), replace=True)
            p_b, km_b = ajustar(X.iloc[idx], k, semente=SEMENTE + b + 1, n_init=5)
            aris.append(adjusted_rand_score(lab, prever(p_b, km_b, X)))
        linhas.append(dict(k=k, inercia=km.inertia_, silhueta=sil, calinski=calinski_harabasz_score(Z, lab),
                           davies=davies_bouldin_score(Z, lab), ari_bootstrap=np.mean(aris), ari_min=np.min(aris),
                           menor_grupo_pct=100 * np.bincount(lab).min() / len(lab)))
        print(f"[k={k}] silhueta {sil:.3f} · CH {linhas[-1]['calinski']:.0f} · DB {linhas[-1]['davies']:.3f} · ARI bootstrap {np.mean(aris):.3f} (mín {np.min(aris):.3f})")
    return pd.DataFrame(linhas)


def grafico_k(t: pd.DataFrame, caminho: Path, k_escolhido: int | None) -> None:
    fundo, tinta, suave, azul, laranja = "#fcfcfb", "#0b0b0b", "#52514e", "#2a78d6", "#eb6834"
    fig, eixos = plt.subplots(1, 3, figsize=(13, 3.8), facecolor=fundo)
    for ax, col, titulo, cor in [(eixos[0], "inercia", "Inércia (cotovelo)", azul), (eixos[1], "silhueta", "Silhueta (maior é melhor)", azul),
                                 (eixos[2], "ari_bootstrap", "Estabilidade: ARI médio no bootstrap", laranja)]:
        ax.set_facecolor(fundo)
        ax.plot(t["k"], t[col], color=cor, lw=2, marker="o", ms=5)
        if k_escolhido:
            ax.axvline(k_escolhido, color=suave, lw=1, ls=":")
        ax.set_title(titulo, fontsize=10, color=tinta, loc="left")
        ax.set_xlabel("k (número de grupos)", fontsize=8, color=suave)
        ax.tick_params(colors=suave, labelsize=8)
        ax.grid(axis="y", color="#e6e5e0", lw=0.6)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        for sp in ("left", "bottom"):
            ax.spines[sp].set_color("#c9c8c2")
    if k_escolhido:
        eixos[2].text(k_escolhido + 0.1, eixos[2].get_ylim()[0], f" k = {k_escolhido}", color=suave, fontsize=8, va="bottom")
    fig.tight_layout()
    fig.savefig(caminho, dpi=150, facecolor=fundo)


def pct_ar_livre_30jun() -> pd.Series:
    t = pd.read_parquet(TREINOS_V2, columns=["user_id", "inicio", "tipo"])
    t = t[pd.to_datetime(t["inicio"]) <= pd.Timestamp("2026-06-30 23:59:59")]
    return (100 * t["tipo"].isin(AR_LIVRE).groupby(t["user_id"]).mean()).round(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=None)
    k = ap.parse_args().k
    hash_master = sha(MASTER)
    m, a, log = carregar()
    comp = a[a["completo"]].reset_index(drop=True)
    X = comp[VARS].astype(float)
    print(f"[população] ativos {n(len(a))} → completos {n(len(comp))} (incompletos {n(int((~a['completo']).sum()))})")

    tk = escolha_k(X)
    tk.to_csv(PROC / "segmentacao_escolha_k.csv", index=False)
    grafico_k(tk, SAIDAS / "segmentacao_escolha_k.png", k)
    if k is None:
        print("[escolha de k] tabela em dados/processados/segmentacao_escolha_k.csv; rode de novo com --k <valor>")
        return

    # modelo final
    prep, km = ajustar(X, k)
    ref = km.labels_
    ordem = np.argsort(-np.bincount(ref))  # grupo 1 = o maior
    renome = {int(old): i + 1 for i, old in enumerate(ordem)}
    comp["grupo"] = [renome[int(c)] for c in ref]
    print(f"[modelo k={k}] tamanhos: {comp['grupo'].value_counts().sort_index().to_dict()}")

    # validação cruzada (K-fold)
    kf = KFold(n_splits=5, shuffle=True, random_state=SEMENTE)
    ari_fold, jac_fold = [], []
    for i, (tr, te) in enumerate(kf.split(X)):
        p_f, km_f = ajustar(X.iloc[tr], k, semente=SEMENTE + 100 + i)
        pred = prever(p_f, km_f, X.iloc[te])
        ari_fold.append(adjusted_rand_score(ref[te], pred))
        jac_fold.append(jaccard_por_grupo(ref[te], pred, k))
    # bootstrap
    rng = np.random.default_rng(SEMENTE)
    ari_boot, jac_boot = [], []
    for b in range(50):
        idx = rng.choice(len(X), size=len(X), replace=True)
        p_b, km_b = ajustar(X.iloc[idx], k, semente=SEMENTE + 200 + b, n_init=10)
        pred = prever(p_b, km_b, X)
        ari_boot.append(adjusted_rand_score(ref, pred))
        jac_boot.append(jaccard_por_grupo(ref, pred, k))
    # sementes
    ari_sem = []
    for s in range(20):
        _, km_s = ajustar(X, k, semente=1000 + s, n_init=1)
        ari_sem.append(adjusted_rand_score(ref, km_s.labels_))
    jf, jb = np.mean(jac_fold, axis=0), np.mean(jac_boot, axis=0)
    print(f"[validação] ARI K-fold {np.mean(ari_fold):.3f} (mín {np.min(ari_fold):.3f}) · bootstrap {np.mean(ari_boot):.3f} "
          f"(p5 {np.percentile(ari_boot, 5):.3f}) · sementes {np.mean(ari_sem):.3f} (mín {np.min(ari_sem):.3f})")

    # incompletas classificadas pelo centro mais próximo (não formam grupos)
    inc = a[~a["completo"]].copy()
    inc["grupo"] = [renome[int(c)] for c in prever(prep, km, inc[VARS].astype(float))]

    # viés: completas x incompletas (diferença padronizada de médias)
    a["minutos_por_treino_90d"] = a["minutos_por_treino_90d"].astype(float)
    a["mensal"] = a["plano_atual"].eq("mensal")
    a["renov_desl"] = a["renovacao_desligada"].fillna(False).astype(bool)
    vies_vars = VARS + ["mensal", "renov_desl", "pg_pct_recusa", "n_tickets_90d"]
    vies = []
    for c in vies_vars:
        x1, x0 = a.loc[a["completo"], c].astype(float), a.loc[~a["completo"], c].astype(float)
        dp = np.sqrt((x1.var() + x0.var()) / 2)
        vies.append([c, g(x1.mean(), 2), g(x0.mean(), 2), g((x1.mean() - x0.mean()) / dp if dp else 0, 2)])
    smd_max = max(abs(float(v[3].replace(",", "."))) for v in vies)

    # perfil dos grupos (completas)
    base_perfil = comp.copy()
    base_perfil["mensal"] = base_perfil["plano_atual"].eq("mensal")
    base_perfil["renov_desl"] = base_perfil["renovacao_desligada"].fillna(False).astype(bool)
    perfil = base_perfil.groupby("grupo").agg(
        contas=("user_id", "size"), treinos_90d=("treinos_90d", "median"), min_por_treino=("minutos_por_treino_90d", "median"),
        recencia=("recencia_dias", "median"), tendencia=("tendencia", "median"), pct_ar_livre=("pct_ar_livre", "median"),
        modalidades=("n_modalidades_90d", "median"), pct_relogio=("pct_relogio_90d", "median"), sessoes_3m=("sessoes_app_3m", "median"),
        seguidores=("n_seguidores", "median"), posts_90d=("n_posts_90d", "median"))
    descr = base_perfil.groupby("grupo").agg(
        pct_mensal=("mensal", "mean"), pct_renov_desl=("renov_desl", "mean"), idade=("idade", "median"),
        pct_feminino=("sexo", lambda s: (s == "F").mean()), pct_tickets=("n_tickets_90d", lambda s: (s > 0).mean()),
        recusa=("pg_pct_recusa", "mean"), tipo_principal=("tipo_principal", lambda s: s.mode().iat[0]),
        canal=("canal_cobranca", lambda s: s.mode().iat[0]), nivel=("nivel_declarado", lambda s: s.mode().iat[0]))
    camp = pd.crosstab(base_perfil["grupo"], base_perfil["grupo_campanha"], normalize="index")

    # aplicação no corte de 30/06 (só descreve: estabilidade no tempo e saída em 60 dias)
    b6 = pd.read_parquet(BASE_30JUN)
    b6["minutos_por_treino_90d"] = np.where(b6["treinos_90d"] > 0, b6["minutos_90d"] / b6["treinos_90d"].where(b6["treinos_90d"] > 0), 0.0)
    b6 = b6.merge(pct_ar_livre_30jun().rename("pct_ar_livre"), left_on="user_id", right_index=True, how="left")
    b6["pct_ar_livre"] = b6["pct_ar_livre"].fillna(0.0)
    b6["grupo"] = [renome[int(c)] for c in prever(prep, km, b6[VARS].astype(float))]
    saida = b6.groupby("grupo").agg(contas_30jun=("user_id", "size"), saiu_60d=("saiu_60d", "mean"))
    print(f"[30/06] {n(len(b6))} ativos classificados · saída em 60 dias por grupo: " +
          ", ".join(f"{gr}: {100*v:.1f}%" for gr, v in saida["saiu_60d"].items()))

    # gráfico de perfil (centros em z, escala de quem formou os grupos)
    Zc = pd.DataFrame(prep.transform(X), columns=VARS)
    Zc["grupo"] = comp["grupo"].values
    centro = Zc.groupby("grupo")[VARS].mean()
    fig, ax = plt.subplots(figsize=(11, 0.6 * k + 2), facecolor="#fcfcfb")
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("div", ["#2a78d6", "#f0efec", "#eb6834"])
    lim = float(np.abs(centro.values).max())
    im = ax.imshow(centro.values, cmap=cmap, vmin=-lim, vmax=lim, aspect="auto")
    ax.set_xticks(range(len(VARS)))
    ax.set_xticklabels(VARS, rotation=35, ha="right", fontsize=8, color="#52514e")
    ax.set_yticks(range(k))
    ax.set_yticklabels([f"grupo {gr} ({n(perfil.loc[gr, 'contas'])})" for gr in centro.index], fontsize=9, color="#0b0b0b")
    for i in range(k):
        for j in range(len(VARS)):
            ax.text(j, i, f"{centro.values[i, j]:+.1f}".replace(".", ","), ha="center", va="center", fontsize=7, color="#0b0b0b")
    ax.set_title("Centro de cada grupo (desvios-padrão em relação à média; laranja = acima, azul = abaixo)", fontsize=10, loc="left", color="#0b0b0b")
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    fig.tight_layout()
    fig.savefig(SAIDAS / "segmentacao_perfil.png", dpi=150, facecolor="#fcfcfb")

    # saída de dados
    seg = pd.concat([comp[["user_id", "grupo"]].assign(formou_grupo=True), inc[["user_id", "grupo"]].assign(formou_grupo=False)])
    if k == 4:
        seg["persona"] = seg["grupo"].map(PERSONAS)
    seg.to_parquet(PROC / "segmentos_30set.parquet", index=False)
    assert len(seg) == len(a) and seg["user_id"].is_unique

    # relatório
    L = [f"# Segmentação K-means · assinantes ativos em 30/09/2026 (k = {k})\n",
         f"Gerado por `src/segmentacao_kmeans.py --k {k}`. Entrada: `base_master.parquet` (SHA-256 `{hash_master[:16]}…`, não alterada). Grupos formados **sem a variável de saída**; saída aparece só depois, na seção 7.\n",
         "## 1. População (linhas antes e depois)\n", "| passo | linhas antes | linhas depois | observação |", "|---|---|---|---|", *log, "",
         "## 2. Viés da completude: completas × incompletas\n",
         "Diferença padronizada de médias (SMD = diferença ÷ desvio-padrão combinado). |SMD| < 0,1 é desprezível; 0,1 a 0,2 pequeno; acima de 0,2 merece atenção.\n",
         tabela(pd.DataFrame(vies, columns=["variável", f"completas ({n(len(comp))})", f"incompletas ({n(len(inc))})", "SMD"])) + "\n",
         f"Maior |SMD|: **{g(smd_max, 2)}**. " + ("As incompletas se parecem com as completas: o filtro não distorce os grupos." if smd_max < 0.1 else
                                                 "Há diferença pequena: as incompletas são classificadas pelo centro mais próximo (seção 6) para não ficarem de fora da leitura." if smd_max < 0.2 else
                                                 "Há diferença relevante: ler os grupos sabendo que as incompletas são outro perfil (seção 6).") + "\n",
         "## 3. Variáveis do agrupamento\n",
         "Só comportamento (decisão do usuário): perfil (idade, dias por semana declarados, tempo de cadastro) e pagamentos ficam para descrever.\n",
         tabela(pd.DataFrame([[c, "log1p" if c in LOG else "—", "sim"] for c in VARS], columns=["variável", "transformação", "teto p99 + z"])) + "\n",
         "Retiradas antes de agrupar: " + "; ".join(f"`{c}`: {mot}" for c, mot in RETIRADAS.items()) + ".\n",
         "## 4. Escolha de k\n",
         tabela(pd.DataFrame({"k": tk["k"], "inércia": tk["inercia"].map(lambda v: g(v, 0)), "silhueta": tk["silhueta"].map(lambda v: g(v, 3)),
                              "Calinski-Harabasz": tk["calinski"].map(lambda v: g(v, 0)), "Davies-Bouldin": tk["davies"].map(lambda v: g(v, 3)),
                              "ARI bootstrap (10)": tk["ari_bootstrap"].map(lambda v: g(v, 3)), "ARI mínimo": tk["ari_min"].map(lambda v: g(v, 3)),
                              "menor grupo": tk["menor_grupo_pct"].map(lambda v: g(v) + "%")})) + "\n",
         "![escolha de k](segmentacao_escolha_k.png)\n",
         "## 5. Validação cruzada da estabilidade\n",
         tabela(pd.DataFrame([
             ["K-fold (5 dobras): ajusta em 4/5, classifica a dobra de fora", g(np.mean(ari_fold), 3), g(np.min(ari_fold), 3)],
             ["Bootstrap (50 reamostras): ajusta na reamostra, classifica todos", g(np.mean(ari_boot), 3), g(np.percentile(ari_boot, 5), 3) + " (p5)"],
             ["Sementes (20 inicializações, n_init = 1)", g(np.mean(ari_sem), 3), g(np.min(ari_sem), 3)],
         ], columns=["teste", "ARI médio", "pior"])) + "\n",
         "Critério combinado: ARI ≥ 0,8 estável; 0,6 a 0,8 moderado; abaixo de 0,6 instável.\n",
         tabela(pd.DataFrame({"grupo": range(1, k + 1),
                              "Jaccard K-fold": [g(jf[int(ordem[i])], 3) for i in range(k)],
                              "Jaccard bootstrap": [g(jb[int(ordem[i])], 3) for i in range(k)]})) + "\n",
         "Jaccard por grupo: quanto cada grupo se reencontra (≥ 0,75 estável; 0,5 a 0,75 moderado; < 0,5 se desfaz).\n",
         "## 6. Perfil dos grupos (contas completas)\n",
         "Medianas na escala original:\n",
         tabela(perfil.reset_index().assign(**{c: perfil[c].map(lambda v: g(v)) .values for c in perfil.columns if c != "contas"}).assign(contas=perfil["contas"].map(n).values)) + "\n",
         "Descritivas (não formaram os grupos):\n",
         tabela(pd.DataFrame({"grupo": descr.index, "% mensal": (100 * descr["pct_mensal"]).map(g), "% renovação desligada": (100 * descr["pct_renov_desl"]).map(g),
                              "idade (mediana)": descr["idade"].map(g), "% feminino": (100 * descr["pct_feminino"]).map(g),
                              "% com ticket 90d": (100 * descr["pct_tickets"]).map(g), "recusa média (%)": descr["recusa"].map(g),
                              "tipo principal": descr["tipo_principal"], "canal mais comum": descr["canal"], "nível mais comum": descr["nivel"]})) + "\n",
         "Campanha de 10/08 por grupo (sorteio aleatório: as proporções devem ser parecidas entre grupos):\n",
         tabela((100 * camp).round(1).reset_index().astype(str)) + "\n",
         "Incompletas classificadas pelo centro mais próximo (não formaram grupos): " +
         ", ".join(f"grupo {gr}: {n(v)}" for gr, v in inc["grupo"].value_counts().sort_index().items()) + ".\n",
         "![perfil](segmentacao_perfil.png)\n",
         "## 7. Depois de agrupar: estabilidade no tempo e saída em 60 dias (corte de 30/06, só descreve)\n",
         tabela(pd.DataFrame({"grupo": saida.index, "% em 30/09 (completas)": (100 * perfil["contas"] / perfil["contas"].sum()).map(g).values,
                              "contas em 30/06": saida["contas_30jun"].map(n).values, "% em 30/06": (100 * saida["contas_30jun"] / saida["contas_30jun"].sum()).map(g).values,
                              "saiu em 60 dias (30/06)": (100 * saida["saiu_60d"]).map(lambda v: g(v) + "%").values})) + "\n",
         f"Saída média em 60 dias no corte de 30/06: {g(100 * b6['saiu_60d'].mean())}%. A taxa por grupo não foi usada para formar os grupos: só mostra se eles separam risco.\n"]
    if k == 4:
        tam = perfil["contas"]
        L += ["## 8. Personas (leitura do perfil)\n",
              tabela(pd.DataFrame([
                  [1, PERSONAS[1], n(tam[1]), "treina com frequência (mediana de 29 treinos em 90 dias) e registra pelo app, sem relógio; é quem mais abre o app (12,7 sessões por mês)", g(100 * saida.loc[1, "saiu_60d"]) + "%"],
                  [2, PERSONAS[2], n(tam[2]), "treina tanto quanto o grupo 1, mas 78% dos treinos vêm do relógio; abre pouco o app (3,7 sessões) e varia mais de modalidade", g(100 * saida.loc[2, "saiu_60d"]) + "%"],
                  [3, PERSONAS[3], n(tam[3]), "poucos treinos (4 em 90 dias), último há 13 dias, pouco app e quase nada no social; 54% já desligaram a renovação; mais recentes (28% chegaram depois do sorteio de 10/08)", g(100 * saida.loc[3, "saiu_60d"]) + "%"],
                  [4, PERSONAS[4], n(tam[4]), "nenhum treino em 90 dias e quase nenhum uso do app; 99,5% no plano anual (paga e não usa); 35% com renovação desligada", g(100 * saida.loc[4, "saiu_60d"]) + "%"],
              ], columns=["grupo", "persona", "contas (completas)", "o que define", "saiu em 60 dias (30/06)"])) + "\n",
              "Leitura para o negócio (hipóteses, não causa): os grupos 1 e 2 são a base saudável, separados pelo jeito de registrar o treino; o 3 concentra o risco (perto do dobro da saída média) e ainda treina um pouco, então é onde agir tem mais chance; o 4 é o anual que já parou e só sai no aniversário, o que dá prazo para agir antes do vencimento.\n",
              "## 9. Notas\n",
              "- **Sementes com uma única inicialização:** média 0,897, mas o pior caso cai a 0,318: com `n_init = 1` o K-means às vezes para num mínimo local ruim. O modelo final usa `n_init = 20`, e por isso o K-fold e o bootstrap ficam acima de 0,99.",
              "- **Campanha por grupo:** entre os sorteados, os quatro braços têm proporções parecidas em cada grupo; a diferença está em `fora_da_campanha`, maior no grupo 3 porque ele tem mais assinantes que chegaram depois de 10/08.",
              "- **Grupo 4 e o teto da recência:** 90 dias é o teto de quem não treinou na janela; o grupo 4 é, na prática, quem não treinou em 90 dias.",
              "- **Incompletas:** as 3.721 contas sem perfil completo têm o mesmo comportamento das completas (maior |SMD| 0,03) e foram classificadas pelo centro mais próximo, em proporções parecidas.\n",
              "## 10. Decisões propostas (formato do `decisoes.md`, não gravadas)\n",
              "| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |",
              "|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|",
              f"| 39 | 10/11/2026 | base_master | contas sem perfil ou onboarding completo na segmentação | formar os grupos só com as contas completas (sem idade inválida e sem sexo, nível ou dias por semana não informados); classificar as incompletas depois pelo centro mais próximo | pedido do usuário; o viés medido é desprezível (maior SMD {g(smd_max, 2)}) | {n(len(a))} → {n(len(comp))} formam os grupos; {n(len(inc))} classificadas depois |",
              f"| 40 | 10/11/2026 | base_master | variáveis do K-means | só comportamento ({', '.join(VARS)}); teto no p99, log nas contagens e padronização z ajustados no treino; `minutos_90d` (r 0,97) e `n_tickets_90d` (quase constante) fora | perfil e pagamentos repetem plano e cadastro (descritivos); evitar peso duplo e grupos de exceção | {len(VARS)} variáveis; base master inalterada |",
              f"| 41 | 10/11/2026 | base_master | número de grupos | k = 4, pela estabilidade (ARI K-fold {g(np.mean(ari_fold), 3)}, bootstrap {g(np.mean(ari_boot), 3)}) e por Calinski-Harabasz e Davies-Bouldin melhores que k = 3; personas: {', '.join(PERSONAS.values())} | k = 2 tem a maior silhueta, mas só separa ativo de inativo | {n(len(comp))} contas em 4 grupos ({', '.join(n(v) for v in tam.values)}) |"]
    MD.write_text("\n".join(L), encoding="utf-8")
    assert sha(MASTER) == hash_master
    print(f"[saída] {MD.relative_to(RAIZ)} · segmentos_30set.parquet ({n(len(seg))} linhas) · base_master inalterada")


if __name__ == "__main__":
    main()
