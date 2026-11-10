"""Segmentação ampliada dos assinantes ativos em 30/09/2026: perfil + comportamento, dummies ponderadas, VIF e importância.

Uso:
  python src/segmentacao_ampliada.py                 -> imputações, VIF e escolha de k (sem modelo final)
  python src/segmentacao_ampliada.py --k 4           -> importância das variáveis com k = 4, escolha de k no conjunto final
  python src/segmentacao_ampliada.py --k 4 --k-final 5  -> idem, com modelo final em k = 5 (padrão: igual a --k)

Plano aprovado pelo usuário (10/11/2026):
- 14.753 ativos (sem filtro de completude): sexo vazio imputado pelo nome do e-mail; nível vazio = iniciante;
  dias por semana vazios inferidos dos treinos (calibrados com quem declarou); idade fora.
- plano, canal de cobrança, objetivo, sinais de saída e campanha fora do agrupamento.
- categorias reduzidas (uf em 4 blocos, tipo principal em 5) e dummies com peso 1/√m (cada variável categórica pesa o
  mesmo que uma numérica); VIF com remoção iterativa acima de 5; importância por retirada (ARI) e por permutação.
Só lê arquivos; a segmentação atual (segmentos_30set.parquet) não é alterada.
"""

import argparse
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.model_selection import KFold
from statsmodels.stats.outliers_influence import variance_inflation_factor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import segmentacao_kmeans as sk  # noqa: E402
from utils import contas_de_teste  # noqa: E402

n, g, tabela, sha = sk.n, sk.g, sk.tabela, sk.sha
RAIZ, PROC, SAIDAS = sk.RAIZ, sk.PROC, sk.SAIDAS
USUARIOS = RAIZ / "dados" / "brutos" / "usuarios.csv"
MD = SAIDAS / "segmentacao_ampliada.md"
SEMENTE = 42
VIF_LIMITE = 5.0
REGRA_ARI = 0.01  # referência da regra do plano (só no relatório)
REGRA_PERM = 1.0  # decisão do usuário (10/11/2026): sai quem muda menos de 1% das contas na permutação
SOCIAL_FORA = {"n_seguindo": "bloco social reduzido (decisão do usuário): fica `n_seguidores`",
               "n_posts": "bloco social reduzido (decisão do usuário): fica `n_posts_90d`"}

ORIGINAIS = list(sk.VARS)
NUM = ORIGINAIS + ["dias_desde_cadastro", "dias_semana", "nivel_ord", "km_90d", "pct_video", "dias_ativos_mes",
                   "minutos_mes", "pg_pct_recusa", "n_seguindo", "n_posts"]
LOG = set(sk.LOG) | {"km_90d", "minutos_mes", "n_seguindo", "n_posts"}
CAT = ["sexo_final", "sistema", "uf_grupo", "canal_aquisicao", "tipo_grupo", "relogio_conectado", "pg_metodo_principal"]
UF_GRUPO = {"SP": "SP", "RJ": "RJ_MG", "MG": "RJ_MG", "ES": "RJ_MG", "PR": "Sul", "RS": "Sul", "SC": "Sul"}
TIPO_GRUPO = {"corrida": "corrida", "forca": "forca", "caminhada": "caminhada", "pedal": "pedal"}
NIVEL_ORD = {"iniciante": 1, "intermediario": 2, "avancado": 3}
AR_LIVRE, VIDEO = ["corrida", "caminhada", "pedal"], ["funcional", "forca", "yoga", "hiit"]
# nomes dados depois de ler o perfil do modelo final com k = 4 (mesmos perfis da segmentação atual, ARI 0,93)
PERSONAS: dict[int, str] = {1: "Engajado no app", 2: "Engajado com relógio", 3: "Esfriando", 4: "Parado (anual dormente)"}


# ---------------------------------------------------------------- pré-processamento
class Preparo:
    """Numéricas: teto p99 -> log1p nas contagens -> z. Categóricas: one-hot completo, z em cada dummy, peso 1/√m."""

    def __init__(self, num: list[str], cat: list[str], peso: bool = True):
        self.num, self.cat, self.peso = list(num), list(cat), peso

    def fit(self, X: pd.DataFrame) -> "Preparo":
        self.teto = X[self.num].astype(float).quantile(0.99)
        B = self._num(X)
        self.media, self.dp = B.mean(), B.std(ddof=0).replace(0, 1)
        self.niveis = {c: sorted(X[c].astype(str).unique()) for c in self.cat}
        D = self._dum(X)
        self.dmedia, self.ddp = D.mean(), D.std(ddof=0).replace(0, 1)
        self.colunas = self.num + list(D.columns)
        self.var_da_coluna = {c: c for c in self.num} | {d: d.split("=")[0] for d in D.columns}
        return self

    def _num(self, X):
        B = X[self.num].astype(float).clip(upper=self.teto, axis=1)
        for c in self.num:
            if c in LOG:
                B[c] = np.log1p(B[c])
        return B

    def _dum(self, X):
        partes = []
        for c in self.cat:
            v = X[c].astype(str)
            partes.append(pd.DataFrame({f"{c}={lv}": (v == lv).astype(float).values for lv in self.niveis[c]}, index=X.index))
        return pd.concat(partes, axis=1) if partes else pd.DataFrame(index=X.index)

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        Zn = ((self._num(X) - self.media) / self.dp).to_numpy()
        if not self.cat:
            return Zn
        D = (self._dum(X) - self.dmedia) / self.ddp
        if self.peso:
            for c in self.cat:
                cols = [d for d in D.columns if d.startswith(f"{c}=")]
                D[cols] = D[cols] / np.sqrt(len(cols))
        return np.hstack([Zn, D.to_numpy()])


def ajustar(X, num, cat, k, semente=SEMENTE, n_init=20):
    prep = Preparo(num, cat).fit(X)
    km = KMeans(n_clusters=k, n_init=n_init, random_state=semente).fit(prep.transform(X))
    return prep, km


# ---------------------------------------------------------------- imputações
def nome_do_email(local: str, nomes_ordenados: list[str]) -> str | None:
    m = re.match(r"^([a-z]+)[._]", local)
    if m:
        return m.group(1)
    for nm in nomes_ordenados:
        if local.startswith(nm):
            return nm
    return None


def dicionario_nomes(locais: pd.Series, sexo: pd.Series) -> pd.Series:
    """Parcela de mulheres por primeiro nome (só e-mails com nome separado por . ou _ e sexo conhecido)."""
    tok = locais.str.extract(r"^([a-z]+)[._]")[0]
    ok = tok.notna() & sexo.isin(["F", "M"])
    return (sexo[ok] == "F").groupby(tok[ok]).mean()


def prever_sexo(locais: pd.Series, d: pd.Series) -> pd.Series:
    ordem = sorted(d.index, key=len, reverse=True)
    nome = locais.map(lambda l: nome_do_email(l, ordem))
    p = nome.map(d)
    return pd.Series(np.select([p >= 0.9, p <= 0.1], ["F", "M"], default="nao_informado"), index=locais.index), nome


def imputar_sexo(master: pd.DataFrame, log: list) -> tuple[pd.Series, dict]:
    u = pd.read_csv(USUARIOS, dtype=str, keep_default_na=False, usecols=["user_id", "email"])
    teste = contas_de_teste()
    antes = len(u)
    u = u[~u["user_id"].isin(teste)].copy()
    log.append(f"| usuarios.csv (só e-mail) sem contas de teste | {n(antes)} | {n(len(u))} | {n(antes - len(u))} de teste fora |")
    u = u.merge(master[["user_id", "sexo"]], on="user_id", how="left", validate="1:1")
    log.append(f"| ↳ junção com o sexo padronizado da base master (decisão 2) | {n(len(u))} | {n(len(u))} | 1:1 |")
    u["local"] = u["email"].str.strip().str.lower().str.split("@").str[0]
    conhecido = u[u["sexo"].isin(["F", "M"])].reset_index(drop=True)
    # validação cruzada: dicionário montado sem a parte testada
    acertos, cobre = [], []
    for tr, te in KFold(5, shuffle=True, random_state=SEMENTE).split(conhecido):
        d = dicionario_nomes(conhecido.loc[tr, "local"], conhecido.loc[tr, "sexo"])
        pred, _ = prever_sexo(conhecido.loc[te, "local"], d)
        decid = pred != "nao_informado"
        cobre.append(decid.mean())
        acertos.append((pred[decid] == conhecido.loc[te, "sexo"][decid]).mean())
    d = dicionario_nomes(conhecido["local"], conhecido["sexo"])
    pred, nome = prever_sexo(u["local"], d)
    ambiguos = int(((d > 0.1) & (d < 0.9)).sum())
    vazio = u["sexo"].eq("nao_informado")
    u["sexo_final"] = np.where(vazio, pred, u["sexo"])
    u["sexo_imputado"] = vazio & (pred != "nao_informado")
    info = dict(nomes=len(d), ambiguos=ambiguos, acerto=float(np.mean(acertos)), cobertura=float(np.mean(cobre)),
                vazios=int(vazio.sum()), preenchidos=int(u["sexo_imputado"].sum()),
                sobram=int((u["sexo_final"] == "nao_informado").sum()), sem_nome=int(nome.isna().sum()),
                exemplo=d.sort_values().round(3))
    print(f"[sexo] {len(d)} nomes ({ambiguos} ambíguos) · CV acerto {info['acerto']:.4f} cobertura {info['cobertura']:.4f} · "
          f"vazios {info['vazios']} → preenchidos {info['preenchidos']} (sobram {info['sobram']})")
    return u.set_index("user_id")[["sexo_final", "sexo_imputado"]], info


def treinos_no_corte(t: pd.DataFrame, corte: pd.Timestamp) -> pd.DataFrame:
    """Mesma janela da base master: treinos até 23:59:59 do corte; 90 dias = dias < 90."""
    t = t[t["inicio"] <= corte + pd.Timedelta(hours=23, minutes=59, seconds=59)].copy()
    t["dias"] = (corte.normalize() - t["inicio"].dt.normalize()).dt.days
    g90 = t[t["dias"] < 90]
    ct = t.groupby(["user_id", "tipo"]).size().reset_index(name="q")
    principal = ct.loc[ct.groupby("user_id")["q"].idxmax()].set_index("user_id")["tipo"]
    return pd.DataFrame({
        "freq_obs_semana": g90.groupby("user_id")["inicio"].apply(lambda s: s.dt.normalize().nunique()) / (90 / 7),
        "pct_ar_livre_c": (100 * t["tipo"].isin(AR_LIVRE).groupby(t["user_id"]).mean()).round(1),
        "pct_video_c": (100 * t["tipo"].isin(VIDEO).groupby(t["user_id"]).mean()).round(1),
        "tipo_principal_c": principal})


def calibrar_frequencia(a: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Tabela: faixa de frequência observada (0,5/semana, teto 6) -> mediana dos dias declarados (quem declarou)."""
    dec = a[a["dias_semana_declarado"].notna()].copy()
    dec["faixa"] = (dec["freq_obs_semana"].clip(upper=6) * 2).round() / 2
    tab = dec.groupby("faixa").agg(contas=("user_id", "size"), declarado_mediana=("dias_semana_declarado", "median"),
                                   declarado_media=("dias_semana_declarado", "mean"))
    from scipy.stats import spearmanr
    rho = spearmanr(dec["freq_obs_semana"], dec["dias_semana_declarado"]).statistic
    r = np.corrcoef(dec["freq_obs_semana"], dec["dias_semana_declarado"])[0, 1]
    cruz = pd.crosstab(dec["dias_semana_declarado"].astype(int), dec["freq_obs_semana"].clip(upper=6).round().astype(int))
    return tab, dict(rho=rho, r=r, n=len(dec), cruz=cruz)


def aplicar_frequencia(freq_obs: pd.Series, tab: pd.DataFrame) -> pd.Series:
    faixa = (freq_obs.clip(upper=6) * 2).round() / 2
    ok = tab[tab["contas"] >= 30]["declarado_mediana"]
    # faixa com poucas contas usa a faixa válida mais próxima
    return faixa.map(lambda f: ok.iloc[int(np.argmin(np.abs(ok.index.values - f)))])


def montar(base: pd.DataFrame, corte: pd.Timestamp, t: pd.DataFrame, sexo: pd.DataFrame, cad: pd.Series,
           tab_freq: pd.DataFrame | None) -> pd.DataFrame:
    """Variáveis de agrupamento para um corte (30/09 a partir da master; 30/06 a partir da base de assinantes)."""
    a = base.copy()
    tc = treinos_no_corte(t, corte)
    a = a.merge(tc, left_on="user_id", right_index=True, how="left", validate="1:1")
    a["freq_obs_semana"] = a["freq_obs_semana"].fillna(0.0)
    for c in ["pct_ar_livre", "pct_video"]:
        a[c] = a[f"{c}_c"].fillna(0.0)
    a["tipo_principal"] = a["tipo_principal_c"].fillna("sem_treino")
    a["minutos_por_treino_90d"] = np.where(a["treinos_90d"] > 0, a["minutos_90d"] / a["treinos_90d"].where(a["treinos_90d"] > 0), 0.0)
    a["dias_desde_cadastro"] = (corte - a["user_id"].map(cad).dt.normalize()).dt.days.clip(lower=0)
    a = a.merge(sexo, left_on="user_id", right_index=True, how="left", validate="1:1")
    a["nivel_imputado"] = a["nivel_declarado"].eq("nao_informado")
    a["nivel_ord"] = a["nivel_declarado"].map(NIVEL_ORD).fillna(1).astype(float)
    a["dias_semana_imputado"] = a["dias_semana_declarado"].isna()
    if tab_freq is not None:
        a["dias_semana"] = a["dias_semana_declarado"].fillna(aplicar_frequencia(a["freq_obs_semana"], tab_freq))
    a["uf_grupo"] = a["uf"].map(UF_GRUPO).fillna("outras")
    a["tipo_grupo"] = a["tipo_principal"].map(TIPO_GRUPO).fillna("outros")
    return a


# ---------------------------------------------------------------- VIF
def matriz_vif(X: pd.DataFrame, num: list[str], cat: list[str]) -> pd.DataFrame:
    B = X[num].astype(float).clip(upper=X[num].astype(float).quantile(0.99), axis=1)
    for c in num:
        if c in LOG:
            B[c] = np.log1p(B[c])
    B = (B - B.mean()) / B.std(ddof=0).replace(0, 1)
    D = pd.get_dummies(X[cat].astype(str), prefix_sep="=", drop_first=True, dtype=float) if cat else pd.DataFrame(index=X.index)
    return pd.concat([B, D], axis=1)


def vif(M: pd.DataFrame) -> pd.Series:
    A = np.column_stack([np.ones(len(M)), M.to_numpy()])
    return pd.Series([variance_inflation_factor(A, i + 1) for i in range(M.shape[1])], index=M.columns)


def vif_iterativo(X: pd.DataFrame) -> tuple[list[str], list[str], pd.DataFrame, pd.Series, list]:
    num, cat = list(NUM), list(CAT)
    primeiro = vif(matriz_vif(X, num, cat))
    passos = []
    while True:
        M = matriz_vif(X, num, cat)
        v = vif(M)
        var = pd.Series({c: (c if c in num else c.split("=")[0]) for c in M.columns})
        por_var = v.groupby(var).max().sort_values(ascending=False)
        altos = por_var[por_var > VIF_LIMITE]
        if altos.empty:
            break
        novos = [x for x in altos.index if x not in ORIGINAIS]
        sai = novos[0] if novos else altos.index[0]
        col = v[var == sai].idxmax()
        corr = M.corrwith(M[col]).drop([c for c in M.columns if var[c] == sai]).abs().sort_values(ascending=False)
        passos.append([sai, por_var[sai], corr.index[0], corr.iloc[0], altos.index[0]])
        print(f"[VIF] sai {sai} (VIF {por_var[sai]:.1f}; mais correlacionada: {corr.index[0]} |r| {corr.iloc[0]:.2f})")
        (num if sai in num else cat).remove(sai)
    return num, cat, M, v, passos + [["_inicial", primeiro]]


# ---------------------------------------------------------------- escolha de k, importância, estabilidade
def escolha_k(X, num, cat, kmax=10):
    rng = np.random.default_rng(SEMENTE)
    amostra = rng.choice(len(X), size=min(5000, len(X)), replace=False)
    linhas = []
    for k in range(2, kmax + 1):
        prep, km = ajustar(X, num, cat, k)
        Z, lab = prep.transform(X), km.labels_
        aris = []
        for b in range(10):
            idx = rng.choice(len(X), size=len(X), replace=True)
            p_b, km_b = ajustar(X.iloc[idx], num, cat, k, semente=SEMENTE + b + 1, n_init=5)
            aris.append(adjusted_rand_score(lab, km_b.predict(p_b.transform(X))))
        linhas.append(dict(k=k, inercia=km.inertia_, silhueta=silhouette_score(Z[amostra], lab[amostra]),
                           calinski=calinski_harabasz_score(Z, lab), davies=davies_bouldin_score(Z, lab),
                           ari_bootstrap=np.mean(aris), ari_min=np.min(aris), menor_grupo_pct=100 * np.bincount(lab).min() / len(lab)))
        l = linhas[-1]
        print(f"[k={k}] silhueta {l['silhueta']:.3f} · CH {l['calinski']:.0f} · DB {l['davies']:.3f} · ARI boot {l['ari_bootstrap']:.3f} "
              f"(mín {l['ari_min']:.3f}) · menor grupo {l['menor_grupo_pct']:.1f}%")
    return pd.DataFrame(linhas)


def importancia(X, num, cat, k):
    prep, km = ajustar(X, num, cat, k)
    ref = km.labels_
    Z = prep.transform(X)
    rng = np.random.default_rng(SEMENTE)
    linhas = []
    for v in num + cat:
        n2, c2 = [x for x in num if x != v], [x for x in cat if x != v]
        _, km_v = ajustar(X, n2, c2, k, n_init=10)
        ari = adjusted_rand_score(ref, km_v.labels_)
        mud = []
        for r in range(10):
            Xp = X.copy()
            Xp[v] = rng.permutation(Xp[v].to_numpy())
            mud.append(np.mean(km.predict(prep.transform(Xp)) != ref))
        if v in num:
            z = Z[:, prep.colunas.index(v)]
            efeito = pd.Series(z).groupby(ref).apply(lambda s: len(s) * (s.mean() - z.mean()) ** 2).sum() / ((z - z.mean()) ** 2).sum()
            tipo_ef = "η²"
        else:
            ct = pd.crosstab(ref, X[v].astype(str).to_numpy())
            from scipy.stats import chi2_contingency
            chi2 = chi2_contingency(ct)[0]
            efeito = np.sqrt(chi2 / (ct.to_numpy().sum() * (min(ct.shape) - 1)))
            tipo_ef = "V de Cramér"
        linhas.append(dict(variavel=v, tipo="numérica" if v in num else f"categórica ({len(prep.niveis[v])})",
                           queda_ari=1 - ari, pct_mudam=100 * np.mean(mud), efeito=efeito, medida=tipo_ef))
        print(f"[importância] {v}: 1−ARI {1 - ari:.3f} · mudam {100 * np.mean(mud):.1f}% · {tipo_ef} {efeito:.3f}")
    # ruído de base: refazer o modelo completo com outras sementes (nada retirado) já muda parte das contas
    ruido = [1 - adjusted_rand_score(ref, ajustar(X, num, cat, k, semente=SEMENTE + 500 + s, n_init=10)[1].labels_) for s in range(5)]
    limite = max(REGRA_ARI, float(np.max(ruido)))
    print(f"[importância] ruído de base (1−ARI ao refazer sem retirar nada): médio {np.mean(ruido):.3f}, máx {np.max(ruido):.3f} → limite {limite:.3f}")
    t = pd.DataFrame(linhas)
    t["fica"] = (t["pct_mudam"] >= REGRA_PERM) & ~t["variavel"].isin(list(SOCIAL_FORA))
    t.attrs.update(ruido_medio=float(np.mean(ruido)), ruido_max=float(np.max(ruido)), limite=limite)
    return t.sort_values("pct_mudam", ascending=False).reset_index(drop=True)


def estabilidade(X, num, cat, k, ref):
    ari_fold, jac_fold = [], []
    for i, (tr, te) in enumerate(KFold(5, shuffle=True, random_state=SEMENTE).split(X)):
        p_f, km_f = ajustar(X.iloc[tr], num, cat, k, semente=SEMENTE + 100 + i)
        pred = km_f.predict(p_f.transform(X.iloc[te]))
        ari_fold.append(adjusted_rand_score(ref[te], pred))
        jac_fold.append(sk.jaccard_por_grupo(ref[te], pred, k))
    rng = np.random.default_rng(SEMENTE)
    ari_boot, jac_boot = [], []
    for b in range(50):
        idx = rng.choice(len(X), size=len(X), replace=True)
        p_b, km_b = ajustar(X.iloc[idx], num, cat, k, semente=SEMENTE + 200 + b, n_init=10)
        pred = km_b.predict(p_b.transform(X))
        ari_boot.append(adjusted_rand_score(ref, pred))
        jac_boot.append(sk.jaccard_por_grupo(ref, pred, k))
    ari_sem = [adjusted_rand_score(ref, ajustar(X, num, cat, k, semente=1000 + s, n_init=1)[1].labels_) for s in range(20)]
    return dict(ari_fold=ari_fold, ari_boot=ari_boot, ari_sem=ari_sem, jac_fold=np.mean(jac_fold, axis=0),
                jac_boot=np.mean(jac_boot, axis=0))


# ---------------------------------------------------------------- gráficos
FUNDO, TINTA, SUAVE, AZUL, LARANJA, CINZA = "#fcfcfb", "#0b0b0b", "#52514e", "#2a78d6", "#eb6834", "#b5b3ad"


def _eixo(ax):
    ax.set_facecolor(FUNDO)
    ax.tick_params(colors=SUAVE, labelsize=8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color("#c9c8c2")


def grafico_vif(v0: pd.Series, v1: pd.Series, caminho: Path):
    v0 = v0.sort_values()
    fig, ax = plt.subplots(figsize=(9, 0.22 * len(v0) + 1.5), facecolor=FUNDO)
    _eixo(ax)
    y = np.arange(len(v0))
    ax.barh(y, v0.clip(upper=30).values, color=[LARANJA if c not in v1.index else AZUL for c in v0.index], height=0.6)
    ax.axvline(VIF_LIMITE, color=SUAVE, lw=1, ls=":")
    ax.set_yticks(y)
    ax.set_yticklabels(v0.index, fontsize=7, color=TINTA)
    for i, val in enumerate(v0.values):
        ax.text(min(val, 30) + 0.3, i, g(val, 1) if np.isfinite(val) else "∞", va="center", fontsize=6.5, color=SUAVE)
    ax.set_xlabel("VIF no conjunto inicial (barras cortadas em 30); laranja = coluna retirada, azul = ficou", fontsize=8, color=SUAVE)
    ax.set_title(f"VIF das candidatas (limite {g(VIF_LIMITE, 0)}, linha pontilhada)", fontsize=10, color=TINTA, loc="left")
    fig.tight_layout()
    fig.savefig(caminho, dpi=150, facecolor=FUNDO)
    plt.close(fig)


def grafico_corr(M: pd.DataFrame, caminho: Path):
    C = M.corr()
    fig, ax = plt.subplots(figsize=(12, 10), facecolor=FUNDO)
    cmap = LinearSegmentedColormap.from_list("div", [AZUL, "#f0efec", LARANJA])
    im = ax.imshow(C.values, cmap=cmap, vmin=-1, vmax=1)
    ax.set_xticks(range(len(C)))
    ax.set_xticklabels(C.columns, rotation=90, fontsize=6, color=SUAVE)
    ax.set_yticks(range(len(C)))
    ax.set_yticklabels(C.index, fontsize=6, color=SUAVE)
    for i in range(len(C)):
        for j in range(len(C)):
            if i != j and abs(C.values[i, j]) >= 0.5:
                ax.text(j, i, f"{C.values[i, j]:.1f}".replace(".", ","), ha="center", va="center", fontsize=5, color=TINTA)
    ax.set_title("Correlação entre as candidatas (escala transformada; números só quando |r| ≥ 0,5)", fontsize=10, loc="left", color=TINTA)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.01)
    fig.tight_layout()
    fig.savefig(caminho, dpi=150, facecolor=FUNDO)
    plt.close(fig)


def grafico_importancia(t: pd.DataFrame, caminho: Path):
    t = t.sort_values("pct_mudam")
    fig, eixos = plt.subplots(1, 2, figsize=(12, 0.3 * len(t) + 1.6), facecolor=FUNDO, sharey=True)
    y = np.arange(len(t))
    cores = [AZUL if f else CINZA for f in t["fica"]]
    for ax, col, lim, titulo in [(eixos[0], "pct_mudam", REGRA_PERM, "Permutação: % das contas que mudam de grupo"),
                                 (eixos[1], "queda_ari", REGRA_ARI, "Retirada: 1 − ARI com o modelo completo")]:
        _eixo(ax)
        ax.barh(y, t[col].values, color=cores, height=0.6)
        ax.axvline(lim, color=SUAVE, lw=1, ls=":")
        ax.set_title(titulo, fontsize=9.5, color=TINTA, loc="left")
        for i, val in enumerate(t[col].values):
            ax.text(val, i, " " + g(val, 1 if col == "pct_mudam" else 3), va="center", fontsize=6.5, color=SUAVE)
    eixos[0].set_yticks(y)
    eixos[0].set_yticklabels(t["variavel"], fontsize=8, color=TINTA)
    fig.suptitle("Importância das variáveis para os grupos (azul = fica; cinza = sai: permutação < 1% ou bloco social reduzido)",
                 fontsize=10, color=TINTA, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(caminho, dpi=150, facecolor=FUNDO)
    plt.close(fig)


def grafico_perfil(prep, X, grupo, tam, caminho: Path):
    Z = pd.DataFrame(prep.transform(X), columns=prep.colunas)
    # para leitura, dummies voltam à escala z sem o peso (o peso só serve para a distância)
    for c in prep.cat:
        cols = [d for d in prep.colunas if d.startswith(f"{c}=")]
        Z[cols] = Z[cols] * np.sqrt(len(cols))
    centro = Z.groupby(np.asarray(grupo)).mean()
    k = len(centro)
    fig, ax = plt.subplots(figsize=(max(12, 0.32 * len(prep.colunas)), 0.6 * k + 3), facecolor=FUNDO)
    cmap = LinearSegmentedColormap.from_list("div", [AZUL, "#f0efec", LARANJA])
    lim = min(2.0, float(np.abs(centro.values).max()))
    im = ax.imshow(centro.values, cmap=cmap, vmin=-lim, vmax=lim, aspect="auto")
    ax.set_xticks(range(len(prep.colunas)))
    ax.set_xticklabels(prep.colunas, rotation=60, ha="right", fontsize=7, color=SUAVE)
    ax.set_yticks(range(k))
    ax.set_yticklabels([f"grupo {gr} ({n(tam[gr])})" for gr in centro.index], fontsize=9, color=TINTA)
    for i in range(k):
        for j in range(len(prep.colunas)):
            ax.text(j, i, f"{centro.values[i, j]:+.1f}".replace(".", ","), ha="center", va="center", fontsize=6, color=TINTA)
    ax.set_title("Centro de cada grupo em desvios-padrão (laranja = acima da média; azul = abaixo; cor saturada em ±2)",
                 fontsize=10, loc="left", color=TINTA)
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    fig.tight_layout()
    fig.savefig(caminho, dpi=150, facecolor=FUNDO)
    plt.close(fig)


# ---------------------------------------------------------------- principal
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=None)
    ap.add_argument("--k-final", type=int, default=None)
    args = ap.parse_args()
    k, k_final = args.k, args.k_final or args.k
    hashes = {p: sha(p) for p in [USUARIOS, sk.MASTER, sk.BASE_30JUN, sk.TREINOS_V2]}
    log: list[str] = []

    m = pd.read_parquet(sk.MASTER)
    log.append(f"| base_master | {n(len(m))} | {n(len(m))} | uma linha por conta |")
    sexo, info_sexo = imputar_sexo(m, log)
    cad = pd.to_datetime(pd.read_csv(USUARIOS, dtype=str, usecols=["user_id", "data_cadastro"]).set_index("user_id")["data_cadastro"])
    t = pd.read_parquet(sk.TREINOS_V2, columns=["user_id", "inicio", "tipo"])
    corte9, corte6 = pd.Timestamp("2026-09-30"), pd.Timestamp("2026-06-30")

    a = m[m["ativo_no_corte"]].copy()
    log.append(f"| ativos em 30/09 (sem teste) | {n(len(m))} | {n(len(a))} | `ativo_no_corte`; sem filtro de completude |")
    a = montar(a, corte9, t, sexo, cad, None)
    log.append(f"| ↳ + treinos no corte, sexo imputado e cadastro (junções 1:1) | {n(len(a))} | {n(len(a))} | linhas inalteradas |")
    # conferência: pct_ar_livre recalculado = base master
    conf_ar = float((a["pct_ar_livre"] - m.set_index("user_id").loc[a["user_id"], "pct_ar_livre"].values).abs().max())
    tab_freq, info_freq = calibrar_frequencia(a)
    a["dias_semana"] = a["dias_semana_declarado"].fillna(aplicar_frequencia(a["freq_obs_semana"], tab_freq))
    print(f"[frequência] declarado × observado: Spearman {info_freq['rho']:.3f} (n {info_freq['n']}); imputados {int(a['dias_semana_imputado'].sum())}")
    print(f"[sexo] ativos com sexo não informado: {int((a['sexo'] == 'nao_informado').sum())} → {int((a['sexo_final'] == 'nao_informado').sum())}")

    # nível: comportamento dos sem nível × níveis declarados
    comp_nivel = a.groupby("nivel_declarado").agg(contas=("user_id", "size"), treinos_90d=("treinos_90d", "median"),
                                                  min_por_treino=("minutos_por_treino_90d", "median"), km_90d=("km_90d", "median"),
                                                  dias_semana_decl=("dias_semana_declarado", "median"),
                                                  freq_obs=("freq_obs_semana", "median"))
    print(comp_nivel.round(2).to_string())

    X = a[NUM + CAT].copy()
    assert not X[NUM].isna().any().any(), X[NUM].isna().sum()[lambda s: s > 0]
    falta_cat = {c: int((X[c].astype(str) == "nao_informado").sum()) for c in CAT}
    log.append(f"| formam os grupos | {n(len(a))} | {n(len(X))} | {n(len(a) - 11032)} a mais que na segmentação atual (11.032) |")

    # VIF
    num_v, cat_v, M_fim, v_fim, passos = vif_iterativo(X)
    v_ini = passos.pop()[1]
    M_ini = matriz_vif(X, NUM, CAT)
    grafico_vif(v_ini, v_fim, SAIDAS / "segmentacao_ampliada_vif.png")
    grafico_corr(M_ini, SAIDAS / "segmentacao_ampliada_correlacao.png")
    print(f"[VIF] ficam {len(num_v)} numéricas e {len(cat_v)} categóricas; maior VIF final {v_fim.max():.2f}")

    tk = escolha_k(X, num_v, cat_v) if k is None else None
    if k is None:
        tk.to_csv(PROC / "segmentacao_ampliada_escolha_k_vif.csv", index=False)
        sk.grafico_k(tk, SAIDAS / "segmentacao_ampliada_escolha_k.png", None)
        print("[parada] rode de novo com --k <valor> para a importância e o modelo final")
        return

    imp = importancia(X, num_v, cat_v, k)
    num_f = [v for v in num_v if imp.set_index("variavel").loc[v, "fica"]]
    cat_f = [v for v in cat_v if imp.set_index("variavel").loc[v, "fica"]]
    grafico_importancia(imp, SAIDAS / "segmentacao_ampliada_importancia.png")
    print(f"[importância] ficam {num_f + cat_f}")
    tk = escolha_k(X, num_f, cat_f)
    tk.to_csv(PROC / "segmentacao_ampliada_escolha_k.csv", index=False)
    sk.grafico_k(tk, SAIDAS / "segmentacao_ampliada_escolha_k.png", k_final)

    # modelo final
    prep, km = ajustar(X, num_f, cat_f, k_final)
    ordem = np.argsort(-np.bincount(km.labels_))
    renome = {int(o): i + 1 for i, o in enumerate(ordem)}
    ref = km.labels_
    a["grupo"] = [renome[int(c)] for c in ref]
    tam = a["grupo"].value_counts().sort_index()
    est = estabilidade(X, num_f, cat_f, k_final, ref)
    print(f"[validação] ARI K-fold {np.mean(est['ari_fold']):.3f} · bootstrap {np.mean(est['ari_boot']):.3f} (p5 {np.percentile(est['ari_boot'], 5):.3f}) · "
          f"sementes {np.mean(est['ari_sem']):.3f} (mín {np.min(est['ari_sem']):.3f}) · tamanhos {tam.to_dict()}")
    grafico_perfil(prep, X, a["grupo"].values, tam, SAIDAS / "segmentacao_ampliada_perfil.png")

    # comparação com a segmentação atual
    atual = pd.read_parquet(PROC / "segmentos_30set.parquet")
    cmp = a[["user_id", "grupo"]].merge(atual.rename(columns={"grupo": "grupo_atual"}), on="user_id", how="inner", validate="1:1")
    ari_atual_comp = adjusted_rand_score(cmp.loc[cmp["formou_grupo"], "grupo_atual"], cmp.loc[cmp["formou_grupo"], "grupo"])
    ari_atual_todos = adjusted_rand_score(cmp["grupo_atual"], cmp["grupo"])
    cruz = pd.crosstab(cmp["persona"], cmp["grupo"])
    print(f"[comparação] ARI com a segmentação atual: completas {ari_atual_comp:.3f} · todas {ari_atual_todos:.3f}")
    print(cruz.to_string())

    # perfil descritivo
    a["mensal"] = a["plano_atual"].eq("mensal")
    a["renov_desl"] = a["renovacao_desligada"].fillna(False).astype(bool)
    med_num = a.groupby("grupo")[num_f].median()
    descr = a.groupby("grupo").agg(
        contas=("user_id", "size"), pct_mensal=("mensal", "mean"), pct_renov_desl=("renov_desl", "mean"), idade=("idade", "median"),
        pct_feminino=("sexo_final", lambda s: (s == "F").mean()), pct_ios=("sistema", lambda s: (s == "ios").mean()),
        tipo=("tipo_grupo", lambda s: s.mode().iat[0]), uf=("uf_grupo", lambda s: s.mode().iat[0]),
        canal=("canal_aquisicao", lambda s: s.mode().iat[0]), relogio=("relogio_conectado", lambda s: s.mode().iat[0]),
        nivel=("nivel_ord", "mean"), dias_semana=("dias_semana", "median"))
    dist_cat = {c: pd.crosstab(a["grupo"], a[c], normalize="index") for c in cat_f}

    # 30/06: estabilidade no tempo e saída em 60 dias (só descreve)
    b6 = pd.read_parquet(sk.BASE_30JUN)
    n6 = len(b6)
    b6 = montar(b6, corte6, t, sexo, cad, tab_freq)
    assert len(b6) == n6
    b6["grupo"] = [renome[int(c)] for c in km.predict(prep.transform(b6[num_f + cat_f]))]
    saida = b6.groupby("grupo").agg(contas_30jun=("user_id", "size"), saiu_60d=("saiu_60d", "mean"))
    print(f"[30/06] {n(len(b6))} ativos · saída em 60 dias: " + ", ".join(f"{gr}: {100 * v:.1f}%" for gr, v in saida["saiu_60d"].items()))

    # saídas de dados
    pers = PERSONAS if len(PERSONAS) == k_final else {}
    seg = a[["user_id", "grupo"]].assign(persona=a["grupo"].map(pers) if pers else None)
    seg.to_parquet(PROC / "segmentos_ampliada_30set.parquet", index=False)
    perfil_imp = a[["user_id", "sexo_final", "sexo_imputado", "nivel_ord", "nivel_imputado", "dias_semana", "dias_semana_imputado",
                    "freq_obs_semana", "uf_grupo", "tipo_grupo"]]
    perfil_imp.to_parquet(PROC / "perfil_imputado.parquet", index=False)
    assert seg["user_id"].is_unique and len(seg) == len(a)

    # ------------------------------------------------------------ relatório
    L = ["# Segmentação ampliada · perfil + comportamento (ativos em 30/09/2026)\n",
         f"Gerado por `src/segmentacao_ampliada.py --k {k}" + (f" --k-final {k_final}" if k_final != k else "") + "`. "
         "Só leitura (SHA-256 de `usuarios.csv`, `base_master`, base de 30/06 e `atividades_limpa_v2` conferidos antes e depois). "
         "A segmentação atual (`segmentos_30set.parquet`, decisões 39 a 41) não foi alterada.\n",
         "## 1. Contas\n", tabela(pd.DataFrame([r.strip("| ").split(" | ") for r in log], columns=["passo", "antes", "depois", "observação"])) + "\n",
         "O filtro de completude da decisão 39 deixa de existir: idade sai do agrupamento e os vazios de sexo, nível e dias por semana são preenchidos (seção 2). "
         f"Todas as {n(len(a))} contas ativas formam os grupos.\n",
         "## 2. Imputações (cada valor preenchido tem marca `*_imputado` em `dados/processados/perfil_imputado.parquet`)\n",
         "### 2.1 Sexo pelo nome do e-mail\n",
         f"O `sexo` padronizado (decisão 2) vem da base master. Para os vazios, o primeiro nome é tirado do e-mail (antes de `.` ou `_`; "
         f"se o nome vem colado, o nome conhecido mais longo no início). A lista nome → sexo é montada com as contas que informaram o sexo.\n",
         tabela(pd.DataFrame([
             ["nomes distintos na lista", n(info_sexo["nomes"])],
             ["nomes ambíguos (entre 10% e 90% de mulheres)", n(info_sexo["ambiguos"])],
             ["acerto na validação cruzada (5 partes, lista sem a parte testada)", f"{g(100 * info_sexo['acerto'], 2)}%"],
             ["cobertura na validação cruzada", f"{g(100 * info_sexo['cobertura'], 2)}%"],
             ["contas com sexo vazio (todas, sem teste)", n(info_sexo["vazios"])],
             ["preenchidas", n(info_sexo["preenchidos"])],
             ["ainda não informado", n(info_sexo["sobram"])],
             ["ativos em 30/09 com sexo vazio → depois", f"{n(int((a['sexo'] == 'nao_informado').sum()))} → {n(int((a['sexo_final'] == 'nao_informado').sum()))}"],
         ], columns=["medida", "valor"])) + "\n",
         "Cuidado: é inferência pelo nome, não o sexo declarado. Serve para não perder a conta no agrupamento; não deve ser usada como dado pessoal da conta.\n",
         "### 2.2 Nível vazio → iniciante (regra do usuário)\n",
         tabela(pd.DataFrame({"nível declarado": comp_nivel.index, "contas": comp_nivel["contas"].map(n).values,
                              "treinos 90d (mediana)": comp_nivel["treinos_90d"].map(g).values,
                              "min por treino (mediana)": comp_nivel["min_por_treino"].map(g).values,
                              "km 90d (mediana)": comp_nivel["km_90d"].map(g).values,
                              "frequência observada/semana (mediana)": comp_nivel["freq_obs"].map(lambda x: g(x, 2)).values})) + "\n"]
    cn = comp_nivel["treinos_90d"]
    perto = (cn.drop("nao_informado") - cn["nao_informado"]).abs().idxmin()
    L.append(f"Pelo número de treinos, quem não informou o nível se parece mais com **{perto}**. A regra do usuário foi aplicada mesmo assim "
             f"({n(int(a['nivel_imputado'].sum()))} contas → iniciante, `nivel_imputado`). Nível entra como ordinal (iniciante 1, intermediário 2, avançado 3), uma coluna só.\n")
    L.append("### 2.3 Dias por semana inferidos dos treinos\n")
    L.append(f"Frequência observada = dias distintos com treino nos 90 dias antes do corte ÷ (90/7). Calibração com as {n(info_freq['n'])} contas que declararam: "
             f"Spearman **{g(info_freq['rho'], 3)}**, Pearson {g(info_freq['r'], 3)}. Para não misturar intenção (declarado) com comportamento (observado), "
             "o vazio recebe a **mediana do declarado** entre quem tem a mesma faixa de frequência observada (faixas de 0,5/semana; faixa com menos de 30 contas usa a vizinha):\n")
    L.append(tabela(pd.DataFrame({"frequência observada (faixa)": tab_freq.index.map(lambda x: g(x, 1)),
                                  "contas que declararam": tab_freq["contas"].map(n).values,
                                  "declarado (mediana)": tab_freq["declarado_mediana"].map(lambda x: g(x, 0)).values,
                                  "declarado (média)": tab_freq["declarado_media"].map(lambda x: g(x, 2)).values})) + "\n")
    cz = info_freq["cruz"]
    L.append("Cruzamento declarado (linhas) × observado arredondado (colunas, teto 6):\n")
    L.append(tabela(cz.reset_index().rename(columns={"dias_semana_declarado": "declarado"})) + "\n")
    L.append(f"Imputados: {n(int(a['dias_semana_imputado'].sum()))} ativos (`dias_semana_imputado`). "
             + ("A correlação é fraca: o declarado é intenção e pouco diz do treino real; a imputação devolve um valor típico, não a verdade da conta." if info_freq["rho"] < 0.3 else
                "A correlação é moderada: a imputação é razoável, mas é estimativa." if info_freq["rho"] < 0.6 else
                "A correlação é forte: a imputação pelo treino é confiável.") + "\n")

    L.append("## 3. Candidatas e redução das categorias\n")
    L.append(f"{len(NUM)} numéricas ({len(ORIGINAIS)} da segmentação atual + {len(NUM) - len(ORIGINAIS)} novas) e {len(CAT)} categóricas. "
             "Fora: idade, plano, canal de cobrança, objetivo, sinais de saída e campanha (decisões do usuário e da base master).\n")
    L.append(tabela(pd.DataFrame([
        ["`sexo_final`", "F, M (+ não informado se sobrar)", ", ".join(f"{k_}: {n(v_)}" for k_, v_ in a["sexo_final"].value_counts().items())],
        ["`sistema`", "android, ios", ", ".join(f"{k_}: {n(v_)}" for k_, v_ in a["sistema"].value_counts().items())],
        ["`uf_grupo`", "11 UF → SP, RJ_MG, Sul, outras", ", ".join(f"{k_}: {n(v_)}" for k_, v_ in a["uf_grupo"].value_counts().items())],
        ["`canal_aquisicao`", "6 (nenhuma abaixo de 9%)", ", ".join(f"{k_}: {n(v_)}" for k_, v_ in a["canal_aquisicao"].value_counts().items())],
        ["`tipo_grupo`", "8 → corrida, forca, caminhada, pedal, outros", ", ".join(f"{k_}: {n(v_)}" for k_, v_ in a["tipo_grupo"].value_counts().items())],
        ["`relogio_conectado`", "nenhum, garmin, apple_watch", ", ".join(f"{k_}: {n(v_)}" for k_, v_ in a["relogio_conectado"].value_counts().items())],
        ["`pg_metodo_principal`", "app_store, google_play, cartao, pix_automatico", ", ".join(f"{k_}: {n(v_)}" for k_, v_ in a["pg_metodo_principal"].value_counts().items())],
        ["`nivel_ord`", "3 categorias → 1 coluna ordinal", "—"],
    ], columns=["variável", "redução", "contas"])) + "\n")
    L.append("**Peso das dummies:** cada categoria vira uma dummy padronizada (z) multiplicada por 1/√m, em que m é o número de categorias da variável. "
             "Assim a soma das variâncias das m dummies é 1, o mesmo peso de uma numérica, e nenhuma variável categórica parte os grupos sozinha. "
             "Numéricas: teto no p99, log nas contagens assimétricas e z (como na segmentação atual). Tudo ajustado só nos dados de cada ajuste.\n")

    L.append("## 4. Estudo de VIF\n")
    L.append(f"VIF calculado sobre as numéricas transformadas e as dummies sem a categoria de referência, com constante. Regra: enquanto houver variável com VIF > {g(VIF_LIMITE, 0)}, "
             "sai a de maior VIF (o VIF de uma categórica é o maior entre as suas dummies); se houver nova e original acima do limite, sai primeiro a nova, para não perder a base comparável.\n")
    if passos:
        L.append(tabela(pd.DataFrame([[i + 1, f"`{p[0]}`", g(p[1], 1) if np.isfinite(p[1]) else "∞", f"`{p[2]}`", g(p[3], 2)] for i, p in enumerate(passos)],
                                     columns=["rodada", "sai", "VIF", "coluna mais correlacionada", "|r|"])) + "\n")
    else:
        L.append("Nenhuma variável acima do limite: nada saiu.\n")
    vt = pd.DataFrame({"coluna": v_ini.index, "VIF inicial": v_ini.map(lambda x: g(x, 2) if np.isfinite(x) else "∞").values,
                       "VIF final": [g(v_fim[c], 2) if c in v_fim.index else "saiu" for c in v_ini.index]})
    L.append(tabela(vt) + "\n")
    L.append(f"Maior VIF final: **{g(v_fim.max(), 2)}**. ![VIF](segmentacao_ampliada_vif.png)\n")
    L.append("![correlação](segmentacao_ampliada_correlacao.png)\n")

    L.append(f"## 5. Importância das variáveis para os grupos (k = {k})\n")
    L.append("No K-means não existe p-valor como na regressão: os grupos nascem das próprias variáveis, e qualquer teste entre grupos sai significativo. "
             "Por isso a importância é medida de três jeitos:\n")
    L.append("- **Retirada:** o K-means é refeito sem a variável; `1 − ARI` com o modelo completo mostra quanto os grupos dependem dela.")
    L.append("- **Permutação:** a variável é embaralhada (10 vezes) e as contas são reclassificadas pelo centro mais próximo; mede quantas mudam de grupo.")
    L.append("- **Tamanho do efeito:** η² (numéricas) ou V de Cramér (categóricas) entre grupos. Só descreve: é alto por construção.\n")
    L.append(f"Regra do plano: sai se `1 − ARI` < {g(REGRA_ARI, 2)} e menos de 2% mudam na permutação. Ela não discrimina: refazer o modelo completo "
             f"com outra semente, sem retirar nada, já dá `1 − ARI` médio de {g(imp.attrs['ruido_medio'], 3)} (máximo {g(imp.attrs['ruido_max'], 3)}), e as variáveis "
             "fracas ficam logo acima desse ruído. **Regra final (decisão do usuário):** sai a variável que muda menos de "
             f"{g(REGRA_PERM, 0)}% das contas na permutação; a retirada (`1 − ARI`) fica como leitura de apoio. "
             "O bloco social também foi reduzido, para não pesar quatro vezes: " + "; ".join(f"`{c}`: {m}" for c, m in SOCIAL_FORA.items()) + ".\n")
    L.append(tabela(pd.DataFrame({"variável": imp["variavel"].map(lambda x: f"`{x}`"), "tipo": imp["tipo"],
                                  "% mudam (permutação)": imp["pct_mudam"].map(g).values, "1 − ARI (retirada)": imp["queda_ari"].map(lambda x: g(x, 3)).values,
                                  "efeito": [f"{g(e, 3)} ({md})" for e, md in zip(imp["efeito"], imp["medida"])],
                                  "decisão": imp["fica"].map({True: "fica", False: "sai"}).values})) + "\n")
    L.append("![importância](segmentacao_ampliada_importancia.png)\n")
    L.append(f"Conjunto final: {len(num_f)} numéricas ({', '.join(f'`{c}`' for c in num_f)}) e {len(cat_f)} categóricas ({', '.join(f'`{c}`' for c in cat_f) or 'nenhuma'}).\n")

    L.append("## 6. Escolha de k no conjunto final\n")
    tkf = tk.copy()
    L.append(tabela(pd.DataFrame({"k": tkf["k"], "silhueta": tkf["silhueta"].map(lambda x: g(x, 3)), "Calinski-Harabasz": tkf["calinski"].map(lambda x: g(x, 0)),
                                  "Davies-Bouldin": tkf["davies"].map(lambda x: g(x, 3)), "ARI bootstrap": tkf["ari_bootstrap"].map(lambda x: g(x, 3)),
                                  "ARI mín": tkf["ari_min"].map(lambda x: g(x, 3)), "menor grupo %": tkf["menor_grupo_pct"].map(g)})) + "\n")
    L.append("![escolha de k](segmentacao_ampliada_escolha_k.png)\n")

    L.append(f"## 7. Modelo final (k = {k_final}) e validação cruzada\n")
    L.append(tabela(pd.DataFrame([
        ["K-fold (5 partes; centros do treino classificam o teste)", g(np.mean(est["ari_fold"]), 3), g(np.min(est["ari_fold"]), 3)],
        ["bootstrap (50 reamostragens)", g(np.mean(est["ari_boot"]), 3), g(np.percentile(est["ari_boot"], 5), 3) + " (p5)"],
        ["sementes (20 inícios, n_init = 1)", g(np.mean(est["ari_sem"]), 3), g(np.min(est["ari_sem"]), 3)],
    ], columns=["teste", "ARI médio", "pior"])) + "\n")
    L.append(tabela(pd.DataFrame({"grupo": tam.index, "contas": tam.map(n).values, "Jaccard K-fold": [g(x, 3) for x in est["jac_fold"]],
                                  "Jaccard bootstrap": [g(x, 3) for x in est["jac_boot"]]})) + "\n")
    L.append("Medianas das numéricas por grupo (escala original):\n")
    L.append(tabela(med_num.reset_index().rename(columns={"grupo": "grupo"}).pipe(lambda d: d.assign(**{c: d[c].map(g) for c in num_f}))) + "\n")
    for c, dc in dist_cat.items():
        L.append(f"`{c}` por grupo (% das contas do grupo):\n")
        L.append(tabela((100 * dc).round(1).reset_index().astype(str)) + "\n")
    L.append("![perfil](segmentacao_ampliada_perfil.png)\n")
    L.append("Descritivas (não formaram os grupos):\n")
    L.append(tabela(pd.DataFrame({"grupo": descr.index, "contas": descr["contas"].map(n).values, "% mensal": (100 * descr["pct_mensal"]).map(g).values,
                                  "% renovação desligada": (100 * descr["pct_renov_desl"]).map(g).values, "idade (mediana)": descr["idade"].map(g).values,
                                  "% feminino": (100 * descr["pct_feminino"]).map(g).values, "% iOS": (100 * descr["pct_ios"]).map(g).values,
                                  "tipo mais comum": descr["tipo"].values, "região mais comum": descr["uf"].values,
                                  "canal mais comum": descr["canal"].values, "relógio mais comum": descr["relogio"].values,
                                  "nível médio (1–3)": descr["nivel"].map(lambda x: g(x, 2)).values,
                                  "dias/semana (mediana)": descr["dias_semana"].map(g).values})) + "\n")

    L.append("## 8. Comparação com a segmentação atual (decisões 39 a 41)\n")
    L.append(f"ARI entre os grupos novos e os atuais: **{g(ari_atual_comp, 3)}** nas 11.032 contas que formaram os grupos atuais e {g(ari_atual_todos, 3)} nas {n(len(cmp))} contas. "
             "Cruzamento (linhas = persona atual; colunas = grupo novo):\n")
    L.append(tabela(cruz.reset_index().astype(str)) + "\n")

    L.append("## 9. Saída em 60 dias por grupo (corte de 30/06, só descreve)\n")
    L.append(f"Os {n(n6)} ativos de 30/06 foram montados com as mesmas variáveis no corte de 30/06 (treinos até 30/06, cadastro até 30/06, mesma lista de nomes e "
             "mesma tabela de frequência) e classificados pelo centro mais próximo.\n")
    L.append(tabela(pd.DataFrame({"grupo": saida.index, "contas em 30/06": saida["contas_30jun"].map(n).values,
                                  "% em 30/06": (100 * saida["contas_30jun"] / saida["contas_30jun"].sum()).map(g).values,
                                  "% em 30/09": (100 * tam / tam.sum()).reindex(saida.index).map(g).values,
                                  "saiu em 60 dias": (100 * saida["saiu_60d"]).map(lambda x: g(x) + "%").values})) + "\n")
    L.append(f"Amplitude da saída entre grupos: {g(100 * (saida['saiu_60d'].max() - saida['saiu_60d'].min()))} p.p. "
             "(na segmentação atual: 9,8% a 19,4%, amplitude 9,6 p.p.).\n")
    if pers:
        L.append("## 10. Leitura\n")
        L.append(f"- **Perfil não separa assinantes:** sexo, região, canal de aquisição, sistema, método de pagamento e nível mudam menos de 1% das contas de grupo, "
                 "mesmo com peso igual ao de uma numérica. A % de mulheres e a idade mediana são praticamente iguais em todos os grupos.")
        L.append(f"- **Os grupos são os mesmos da segmentação atual** (ARI {g(ari_atual_comp, 3)}), agora sem o filtro de completude: "
                 f"{n(len(a))} contas formam os grupos, contra 11.032. As personas foram mantidas: "
                 + ", ".join(f"{gr} {pers[gr]} ({n(tam[gr])})" for gr in tam.index) + ".")
        L.append("- **Ganhos:** VIF máximo abaixo de 5 (na atual, `treinos_90d` tinha 18,7), todas as contas ativas no ajuste e duas variáveis novas com efeito "
                 "(`dias_desde_cadastro` e `dias_semana`).\n")
        L.append("## 11. Decisões 45 a 47 (gravadas no `decisoes.md` em 10/11/2026)\n")
        L.append("| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |")
        L.append("|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|")
        L.append(f"| 45 | 10/11/2026 | base_master + usuarios.csv + atividades_limpa_v2 | vazios de sexo, nível e dias por semana tiravam contas da segmentação | "
                 f"corrigir na cópia `perfil_imputado.parquet` com marca `*_imputado`: sexo pelo nome do e-mail (acerto {g(100 * info_sexo['acerto'], 1)}% na validação cruzada); "
                 "nível vazio = iniciante; dias por semana = mediana do declarado na mesma faixa de frequência observada; idade fora | pedido do usuário; mantém todas as contas no agrupamento | "
                 f"ativos sem sexo {n(int((a['sexo'] == 'nao_informado').sum()))} → 0; nível {n(int(a['nivel_imputado'].sum()))} → 0; dias por semana {n(int(a['dias_semana_imputado'].sum()))} → 0 |")
        L.append(f"| 46 | 10/11/2026 | base_master | variáveis do K-means ampliado | candidatas com dummies de peso 1/√m; VIF iterativo (> 5 sai: {', '.join(p[0] for p in passos)}); "
                 f"sai quem muda < 1% das contas na permutação; bloco social reduzido (sem `n_seguindo` e `n_posts`) | evitar peso duplo e variáveis sem efeito nos grupos | "
                 f"{len(NUM) + len(CAT)} candidatas → {len(num_f) + len(cat_f)} variáveis |")
        L.append(f"| 47 | 10/11/2026 | base_master | segmentação dos ativos em 30/09 | k = {k_final} (ARI K-fold {g(np.mean(est['ari_fold']), 3)}, bootstrap {g(np.mean(est['ari_boot']), 3)}); "
                 f"`segmentos_ampliada_30set.parquet` passa a ser a segmentação de referência, com as personas atuais | mesmos grupos da atual (ARI {g(ari_atual_comp, 3)}) sem perder contas | "
                 f"11.032 → {n(len(a))} contas nos grupos ({', '.join(n(v) for v in tam.values)}) |\n")
    L.append(f"---\nConferências: `pct_ar_livre` recalculado = base master (maior diferença {g(conf_ar, 3)}); "
             + "; ".join(f"`{p.name}` {'inalterado' if sha(p) == h else 'ALTERADO'}" for p, h in hashes.items()) + ".")
    MD.write_text("\n".join(L), encoding="utf-8")
    print(f"escrito: {MD.relative_to(RAIZ)} · " + " · ".join(f"{p.name} {'ok' if sha(p) == h else 'ALTERADO'}" for p, h in hashes.items()))


if __name__ == "__main__":
    main()
