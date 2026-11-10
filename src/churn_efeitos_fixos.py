"""Estudo do churn com efeitos fixos e comparação com a segmentação K-means (painel de 3 cortes).

Painel: base_assinantes_painel_rotulado.parquet (30/04, 31/05, 30/06; rótulo `saiu_60d`).
1. Logit agrupado com efeito fixo de corte e erro-padrão agrupado por assinante (principal).
2. Efeitos fixos de dois sentidos (assinante + corte), modelo linear de probabilidade, só variáveis
   que mudam no tempo (robustez: controla o que é fixo na pessoa; não prova causa).
   Especificação A = comportamento e contexto; B = A + sinais de saída.
3. Checagem fora do tempo: estima em 30/04 + 31/05, mede a AUC em 30/06.
4. K-means: o modelo validado (k = 4, centros de 30/09) é aplicado a cada corte SEM reajuste;
   saída por segmento, segmento como efeito fixo e comparação variável a variável.
Só lê arquivos de dados/processados/ (nada é alterado). Saídas: saidas/churn_efeitos_fixos.md e .png.
"""

import hashlib
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from linearmodels.panel import PanelOLS
from sklearn.metrics import roc_auc_score

import segmentacao_kmeans as sk

warnings.filterwarnings("ignore")
RAIZ = Path(__file__).resolve().parent.parent
PROC = RAIZ / "dados" / "processados"
SAIDAS = RAIZ / "saidas"
PAINEL = PROC / "base_assinantes_painel_rotulado.parquet"
MD = SAIDAS / "churn_efeitos_fixos.md"
PNG = SAIDAS / "churn_efeitos_fixos.png"

LOG = ["treinos_90d", "minutos_por_treino_90d", "tendencia", "sessoes_app_3m", "n_seguidores", "n_posts_90d",
       "n_tickets_90d", "pg_recusas_90d", "pg_estornos", "tenure_dias"]
CONT_TEMPO = ["treinos_90d", "minutos_por_treino_90d", "recencia_dias", "tendencia", "pct_ar_livre", "n_modalidades_90d",
              "pct_relogio_90d", "sessoes_app_3m", "n_seguidores", "n_posts_90d", "n_tickets_90d", "pg_recusas_90d"]
CONT_FIXAS = ["tenure_dias", "idade", "pg_estornos"]
BIN_A = ["mensal", "flag_email_repetido", "flag_nascimento_invalido"]  # sem_questionario é 0 em todo o painel
CAT_A = {"canal_cobranca": "app_store", "sexo": "F", "sistema": "android", "relogio_conectado": "nenhum",
         "canal_aquisicao": "organico", "nivel_declarado": "intermediario"}
SINAIS_CONT = ["dias_ate_fim_periodo"]  # n_carencia é 0 em todo o painel (nenhum ativo passou por carência antes do corte)
SINAIS_BIN = ["renovacao_desligada", "tem_cancelamento_web"]
NOMES = {"mensal": "plano mensal (× anual)", "renovacao_desligada": "renovação desligada", "tem_cancelamento_web": "cancelamento no site",
         "dias_ate_fim_periodo": "dias até o fim do período", "n_carencia": "eventos de carência"}


def n(x) -> str:
    return f"{int(x):,}".replace(",", ".")


def g(x, d=2) -> str:
    return "—" if pd.isna(x) else f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tabela(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    return "\n".join([cab, sep, *("| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False))])


def sha(c: Path) -> str:
    return hashlib.sha256(c.read_bytes()).hexdigest()


def pct_ar_livre_por_corte(cortes: list[str]) -> pd.DataFrame:
    t = pd.read_parquet(PROC / "atividades_limpa_v2.parquet", columns=["user_id", "inicio", "tipo"])
    t["inicio"] = pd.to_datetime(t["inicio"])
    out = []
    for c in cortes:
        s = t[t["inicio"] <= pd.Timestamp(c) + pd.Timedelta(hours=23, minutes=59, seconds=59)]
        v = (100 * s["tipo"].isin(sk.AR_LIVRE).groupby(s["user_id"]).mean()).rename("pct_ar_livre").reset_index()
        out.append(v.assign(corte=c))
    return pd.concat(out)


def preparar(p: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    d = p.copy()
    d["y"] = d["saiu_60d"].astype(int)
    d["mensal"] = (d["plano_atual"] == "mensal").astype(int)
    d["minutos_por_treino_90d"] = np.where(d["treinos_90d"] > 0, d["minutos_90d"] / d["treinos_90d"].where(d["treinos_90d"] > 0), 0.0)
    d = d.merge(pct_ar_livre_por_corte(sorted(d["corte"].unique())), on=["user_id", "corte"], how="left")
    d["pct_ar_livre"] = d["pct_ar_livre"].fillna(0.0)
    d["idade"] = d["idade"].fillna(d["idade"].median())  # com a marca flag_nascimento_invalido no modelo
    for c in BIN_A + SINAIS_BIN:
        d[c] = d[c].astype(bool).astype(int)
    escala = {}
    for c in CONT_TEMPO + CONT_FIXAS + SINAIS_CONT:
        x = d[c].astype(float)
        if c in LOG:
            x = np.log1p(x.clip(lower=0))
        escala[c] = (x.mean(), x.std(ddof=0))
        d[f"z_{c}"] = (x - escala[c][0]) / escala[c][1]
    return d, escala


def formula(spec: str, extra: str = "") -> str:
    termos = [f"z_{c}" for c in CONT_TEMPO + CONT_FIXAS] + BIN_A + [f"C({c}, Treatment('{ref}'))" for c, ref in CAT_A.items()]
    if spec == "B":
        termos += [f"z_{c}" for c in SINAIS_CONT] + SINAIS_BIN
    return "y ~ " + " + ".join(termos + ["C(corte)"]) + extra


def rotulo(termo: str) -> str:
    t = termo.replace("z_", "")
    if t.startswith("C("):
        var = t[2:t.index(",")]
        nivel = t[t.index("[T.") + 3:-1]
        return f"{var} = {nivel} (× {CAT_A.get(var, '?')})"
    base = NOMES.get(t, t)
    return base + (" (log, 1 dp)" if t in LOG else " (1 dp)" if t in CONT_TEMPO + CONT_FIXAS + SINAIS_CONT else "")


def logit(d: pd.DataFrame, spec: str, extra: str = ""):
    m = smf.logit(formula(spec, extra), data=d).fit(disp=0, maxiter=200, cov_type="cluster",
                                                     cov_kwds={"groups": pd.factorize(d["user_id"])[0]})
    me = m.get_margeff(at="overall").summary_frame()
    tab = pd.DataFrame({"coef": m.params, "p": m.pvalues, "lo": m.conf_int()[0], "hi": m.conf_int()[1]})
    tab["OR"] = np.exp(tab["coef"])
    tab = tab.join(me[["dy/dx", "Conf. Int. Low", "Cont. Int. Hi."]].rename(columns={"dy/dx": "ame", "Conf. Int. Low": "ame_lo", "Cont. Int. Hi.": "ame_hi"}))
    tab = tab.drop(index=[i for i in tab.index if i == "Intercept" or i.startswith("C(corte)") or i.startswith("C(segmento")], errors="ignore")
    return m, tab


def twfe(d: pd.DataFrame, spec: str):
    cols = [f"z_{c}" for c in CONT_TEMPO] + (([f"z_{c}" for c in SINAIS_CONT] + SINAIS_BIN) if spec == "B" else [])
    pdx = d.assign(t=pd.to_datetime(d["corte"])).set_index(["user_id", "t"])
    r = PanelOLS(pdx["y"], pdx[cols], entity_effects=True, time_effects=True, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True)
    return r, pd.DataFrame({"coef": r.params, "p": r.pvalues, "lo": r.conf_int()["lower"], "hi": r.conf_int()["upper"]})


def main() -> None:
    h0 = sha(PAINEL)
    p = pd.read_parquet(PAINEL)
    d, escala = preparar(p)
    usuarios = d["user_id"].nunique()
    varia = d.groupby("user_id")["y"].agg(["min", "max"])
    n_varia = int((varia["min"] != varia["max"]).sum())
    print(f"[painel] {n(len(d))} linhas · {n(usuarios)} assinantes · {n_varia} com saída que varia entre cortes · taxa {100*d['y'].mean():.2f}%")

    # 1. logit agrupado
    mA, tA = logit(d, "A")
    mB, tB = logit(d, "B")
    print(f"[logit] A: pseudo-R² {mA.prsquared:.3f} · B: pseudo-R² {mB.prsquared:.3f}")

    # 2. efeitos fixos de dois sentidos
    rA, fA = twfe(d, "A")
    rB, fB = twfe(d, "B")
    print(f"[TWFE] A: R² dentro {rA.rsquared_within:.4f} · B: R² dentro {rB.rsquared_within:.4f}")

    # 3. fora do tempo
    tr, te = d[d["corte"] < "2026-06-30"], d[d["corte"] == "2026-06-30"]
    # o corte de 30/06 não existe no treino; a AUC só depende da ordem, e o efeito de corte desloca todos por igual
    te = te.assign(corte="2026-05-31")
    auc = {}
    for spec in ["A", "B"]:
        # cancelamento_web só existe a partir de 01/06/2026: é 0 nos cortes de treino
        m_tr = smf.logit(formula(spec).replace(" + tem_cancelamento_web", ""), data=tr).fit(disp=0, maxiter=200)
        auc[spec] = roc_auc_score(te["y"], m_tr.predict(te))
    print(f"[fora do tempo] AUC em 30/06: A {auc['A']:.3f} · B {auc['B']:.3f}")

    # 4. K-means aplicado sem reajuste
    _, a, _ = sk.carregar()
    comp = a[a["completo"]].reset_index(drop=True)
    prep, km = sk.ajustar(comp[sk.VARS].astype(float), 4)
    ordem = np.argsort(-np.bincount(km.labels_))
    renome = {int(old): i + 1 for i, old in enumerate(ordem)}
    seg_salvo = pd.read_parquet(PROC / "segmentos_30set.parquet").set_index("user_id")["grupo"]
    recalc = pd.Series([renome[int(c)] for c in km.labels_], index=comp["user_id"])
    iguais = float((seg_salvo.loc[recalc.index] == recalc).mean())
    print(f"[K-means] modelo refeito igual ao salvo em {100*iguais:.2f}% das contas")
    d["segmento"] = [renome[int(c)] for c in sk.prever(prep, km, d[sk.VARS].astype(float))]
    seg_corte = d.groupby(["segmento", "corte"])["y"].agg(["size", "mean"]).unstack("corte")
    mS, tS = logit(d, "A", extra=" + C(segmento, Treatment(1))")
    seg_coef = pd.DataFrame({"coef": mS.params, "p": mS.pvalues})
    seg_coef = seg_coef[seg_coef.index.str.startswith("C(segmento")]
    lr = 2 * (mS.llf - mA.llf)
    tr_s = d[d["corte"] < "2026-06-30"]
    te_s = d[d["corte"] == "2026-06-30"].assign(corte="2026-05-31")
    m_so = smf.logit("y ~ C(segmento, Treatment(1)) + C(corte)", data=tr_s).fit(disp=0)
    auc_seg = roc_auc_score(te_s["y"], m_so.predict(te_s))
    print(f"[K-means] segmento sobre A: LR {lr:.1f} (3 gl) · AUC só segmento {auc_seg:.3f}")

    # comparação variável a variável
    Zc = pd.DataFrame(prep.transform(comp[sk.VARS].astype(float)), columns=sk.VARS)
    Zc["g"] = [renome[int(c)] for c in km.labels_]
    centros = Zc.groupby("g")[sk.VARS].mean()
    separa = (centros.max() - centros.min())
    comp_t = pd.DataFrame({"separação no K-means (amplitude dos centros, dp)": separa})
    comp_t["efeito no churn, logit A (p.p. por 1 dp)"] = [100 * tA.loc[f"z_{v}", "ame"] for v in sk.VARS]
    comp_t["efeito dentro do assinante, TWFE A (p.p. por 1 dp)"] = [100 * fA.loc[f"z_{v}", "coef"] if f"z_{v}" in fA.index else np.nan for v in sk.VARS]
    comp_t["p (logit A)"] = [tA.loc[f"z_{v}", "p"] for v in sk.VARS]
    comp_t["rank separação"] = comp_t.iloc[:, 0].rank(ascending=False).astype(int)
    comp_t["rank churn"] = comp_t.iloc[:, 1].abs().rank(ascending=False).astype(int)
    rho = comp_t["rank separação"].corr(comp_t["rank churn"], method="spearman")
    print(f"[comparação] correlação de Spearman entre os rankings (separação × churn): {rho:.2f}")

    # gráfico de efeitos (logit A)
    plot = tA.assign(nome=[rotulo(i) for i in tA.index]).sort_values("ame")
    fundo, tinta, suave, azul, laranja = "#fcfcfb", "#0b0b0b", "#52514e", "#2a78d6", "#eb6834"
    fig, ax = plt.subplots(figsize=(11, 0.28 * len(plot) + 1.6), facecolor=fundo)
    ax.set_facecolor(fundo)
    y = np.arange(len(plot))
    cores = ["#c9c8c2" if pv >= 0.05 else (laranja if v > 0 else azul) for v, pv in zip(plot["ame"], plot["p"])]
    ax.errorbar(100 * plot["ame"], y, xerr=[100 * (plot["ame"] - plot["ame_lo"]), 100 * (plot["ame_hi"] - plot["ame"])],
                fmt="none", ecolor="#c9c8c2", elinewidth=1.5)
    ax.scatter(100 * plot["ame"], y, c=cores, s=28, zorder=3)
    ax.axvline(0, color=suave, lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(plot["nome"], fontsize=7.5, color=tinta)
    ax.set_xlabel("efeito na probabilidade de sair em 60 dias (pontos percentuais; IC 95%)", fontsize=8, color=suave)
    ax.set_title("O que acompanha a saída em 60 dias (logit A, efeito fixo de corte)\n"
                 "laranja = aumenta, azul = reduz, cinza = não significativo (p ≥ 0,05)",
                 fontsize=10, color=tinta, loc="left")
    ax.tick_params(colors=suave, labelsize=7.5)
    ax.grid(axis="x", color="#e6e5e0", lw=0.6)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.subplots_adjust(left=0.36, right=0.97, top=0.94, bottom=0.06)
    fig.savefig(PNG, dpi=150, facecolor=fundo)

    # relatório
    def tab_logit(t: pd.DataFrame, top: int | None = None) -> str:
        t = t.assign(abs_=t["ame"].abs()).sort_values("abs_", ascending=False)
        if top:
            t = t.head(top)
        return tabela(pd.DataFrame({"variável": [rotulo(i) for i in t.index], "razão de chances": t["OR"].map(g),
                                    "efeito (p.p.)": (100 * t["ame"]).map(lambda v: g(v, 2)),
                                    "IC 95% (p.p.)": [f"{g(100*l, 2)} a {g(100*h, 2)}" for l, h in zip(t["ame_lo"], t["ame_hi"])],
                                    "p": t["p"].map(lambda v: "< 0,001" if v < 0.001 else g(v, 3))}))

    def tab_fe(t: pd.DataFrame) -> str:
        t = t.assign(abs_=t["coef"].abs()).sort_values("abs_", ascending=False)
        return tabela(pd.DataFrame({"variável": [rotulo(i) for i in t.index], "efeito (p.p.)": (100 * t["coef"]).map(lambda v: g(v, 2)),
                                    "IC 95% (p.p.)": [f"{g(100*l, 2)} a {g(100*h, 2)}" for l, h in zip(t["lo"], t["hi"])],
                                    "p": t["p"].map(lambda v: "< 0,001" if v < 0.001 else g(v, 3))}))

    sig_a = tA[tA["p"] < 0.05].assign(abs_=lambda x: x["ame"].abs()).sort_values("abs_", ascending=False)
    L = ["# Churn: efeitos fixos e comparação com a segmentação K-means\n",
         f"Gerado por `src/churn_efeitos_fixos.py`. Entrada: `base_assinantes_painel_rotulado.parquet` (SHA-256 `{h0[:16]}…`, não alterado). "
         "Cruzamento aponta suspeitos, não prova causa: os efeitos abaixo são associações controladas, não efeitos causais.\n",
         "## 1. Painel\n",
         tabela(pd.DataFrame([
             ["linhas (assinante × corte)", n(len(d))], ["assinantes", n(usuarios)],
             ["assinantes nos 3 cortes", n(int((d.groupby('user_id').size() == 3).sum()))],
             ["assinantes com saída que varia entre cortes (identificam os efeitos fixos por pessoa)", n(n_varia)],
             ["taxa de saída em 60 dias", g(100 * d["y"].mean()) + "%"]], columns=["medida", "valor"])) + "\n",
         "Contínuas padronizadas (1 dp no painel; `log` nas contagens assimétricas). Categóricas contra a referência entre parênteses. "
         "Idade ausente recebe a mediana e a marca `flag_nascimento_invalido` entra no modelo. "
         "`cancelamento_web` só aparece nos eventos a partir de 01/06/2026 (mesma data em que começou a pesquisa de saída): vale só no corte de 30/06 e fica fora do teste fora do tempo. "
         "Fora por não variar no painel: `sem_questionario` (todo assinante ativo respondeu) e `n_carencia` (nenhum ativo tinha passado por carência antes do corte: a carência termina em expiração).\n",
         "## 2. Logit agrupado com efeito fixo de corte (principal)\n",
         f"Erro-padrão agrupado por assinante. Pseudo-R²: A {g(mA.prsquared, 3)}; B {g(mB.prsquared, 3)}. Efeito = mudança média na probabilidade de sair (pontos percentuais).\n",
         "### Especificação A: comportamento e contexto (leitura dos fatores)\n",
         tab_logit(tA) + "\n",
         "![efeitos](churn_efeitos_fixos.png)\n",
         "### Especificação B: A + sinais de saída (10 maiores efeitos)\n",
         tab_logit(tB, top=10) + "\n",
         "## 3. Efeitos fixos de dois sentidos (assinante + corte), só variáveis que mudam no tempo\n",
         f"Modelo linear de probabilidade; erro agrupado por assinante. R² dentro: A {g(rA.rsquared_within, 4)}; B {g(rB.rsquared_within, 4)}. "
         f"Identificado só por quem muda entre cortes ({n(n_varia)} assinantes têm saída variando): plano, canal e perfil saem do modelo.\n",
         "### A\n", tab_fe(fA) + "\n", "### B\n", tab_fe(fB) + "\n",
         "## 4. Fora do tempo (estima em 30/04 e 31/05, mede em 30/06)\n",
         tabela(pd.DataFrame([["A (comportamento e contexto)", g(auc["A"], 3)], ["B (A + sinais de saída)", g(auc["B"], 3)],
                              ["só o segmento do K-means (+ corte)", g(auc_seg, 3)]], columns=["modelo", "AUC em 30/06"])) + "\n",
         "## 5. K-means aplicado ao painel (sem reajuste)\n",
         f"Modelo de 30/09 refeito com a mesma semente: igual ao salvo em `segmentos_30set.parquet` em {g(100*iguais)}% das contas.\n",
         tabela(pd.DataFrame({"segmento": [f"{s} · {sk.PERSONAS[s]}" for s in seg_corte.index],
                              **{f"saída {c[8:]}/{c[5:7]} (n)": [f"{g(100*seg_corte[('mean', c)][s], 1)}% ({n(seg_corte[('size', c)][s])})" for s in seg_corte.index]
                                 for c in sorted(d["corte"].unique())}})) + "\n",
         "Segmento como efeito fixo no logit A (referência: 1, Engajado no app):\n",
         tabela(pd.DataFrame({"segmento": [sk.PERSONAS[int(i[i.index('[T.') + 3:-1])] for i in seg_coef.index],
                              "razão de chances": np.exp(seg_coef["coef"]).map(g).values,
                              "p": seg_coef["p"].map(lambda v: "< 0,001" if v < 0.001 else g(v, 3)).values})) + "\n",
         f"Teste de razão de verossimilhança (A + segmento × A): {g(lr, 1)} com 3 graus de liberdade. " +
         ("O segmento ainda acrescenta informação depois das variáveis." if lr > 7.81 else "O segmento não acrescenta informação: as variáveis já carregam o que ele tem.") + "\n",
         "## 6. Comparação: o que separa os grupos × o que acompanha a saída\n",
         tabela(comp_t.reset_index().rename(columns={"index": "variável"}).assign(**{
             comp_t.columns[0]: comp_t.iloc[:, 0].map(g).values, comp_t.columns[1]: comp_t.iloc[:, 1].map(g).values,
             comp_t.columns[2]: comp_t.iloc[:, 2].map(g).values, "p (logit A)": comp_t["p (logit A)"].map(lambda v: "< 0,001" if v < 0.001 else g(v, 3)).values})) + "\n",
         f"Correlação de Spearman entre os dois rankings: **{g(rho, 2)}**.\n"]
    L.append("## 7. Leitura (associações, não causa)\n")
    L.append("Fatores com efeito significativo (p < 0,05) na especificação A, do maior para o menor: " +
             "; ".join(f"{rotulo(i)} {g(100*r.ame, 1)} p.p." for i, r in sig_a.iterrows()) + ".\n")
    def ef(v):
        return g(100 * tA.loc[v, "ame"], 1)
    L += ["### Síntese da comparação\n",
          f"- **O que mais pesa na saída é o plano:** mensal tem {ef('mensal')} p.p. a mais de chance de sair em 60 dias que o anual, com o resto igual. Nenhuma variável de comportamento chega perto.",
          f"- **Entre os comportamentos, treinar pouco e há mais tempo é o sinal mais forte:** cada 1 dp a mais de treinos em 90 dias muda o risco em {ef('z_treinos_90d')} p.p.; cada 1 dp a mais de recência, em +{ef('z_recencia_dias')} p.p. Variar de modalidade ({ef('z_n_modalidades_90d')} p.p.) e tendência de alta ({ef('z_tendencia')} p.p.) também protegem.",
          "- **Com o volume de treino controlado, mais app, mais posts e treinos mais longos acompanham mais saída:** com o mesmo número de treinos, quem abre mais o app ou posta mais sai mais; provavelmente é efeito de supressão entre variáveis correlacionadas (app e posts andam com treinos), e não deve ser lido sozinho.",
          f"- **Dentro da mesma pessoa, quase nada de comportamento muda o risco** (efeitos fixos de dois sentidos): o que separa quem sai de quem fica é diferença entre pessoas, não uma queda recente de uso. Só os sinais mecânicos (renovação desligada {g(100*fB.loc['renovacao_desligada','coef'],1)} p.p.; cancelamento no site {g(100*fB.loc['tem_cancelamento_web','coef'],1)} p.p.) aparecem com força dentro do assinante.",
          f"- **O K-means separa pelas mesmas variáveis que pesam no churn** (correlação dos rankings {g(rho, 2)}): treinos, recência e intensidade estão no topo dos dois. Ele não separa por plano, que é o maior fator, porque plano ficou fora do agrupamento de propósito.",
          f"- **O segmento ainda acrescenta informação** depois das variáveis (razão de verossimilhança {g(lr, 1)}): *Esfriando* tem razão de chances {g(float(np.exp(seg_coef['coef'].iloc[1])), 2)} contra *Engajado no app*. *Parado* fica abaixo ({g(float(np.exp(seg_coef['coef'].iloc[2])), 2)}) porque é quase todo anual e só pode sair no aniversário.",
          f"- **Para prever, segmento sozinho é fraco** (AUC {g(auc_seg, 3)} fora do tempo) contra {g(auc['A'], 3)} do modelo A e {g(auc['B'], 3)} do B: a segmentação serve para entender e falar com cada grupo; a previsão de quem sai pede o modelo com as variáveis (objetivo 4).\n"]
    L.append("## 8. Decisões 42 a 44 (gravadas no `decisoes.md` em 10/11/2026)\n")
    L += ["| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |",
          "|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|",
          f"| 42 | 10/11/2026 | base_assinantes_painel_rotulado | estimar o que acompanha a saída sem misturar cortes | logit agrupado com efeito fixo de corte e erro agrupado por assinante (principal); efeitos fixos de dois sentidos só como robustez | plano, canal e perfil não mudam dentro do assinante; só {n(n_varia)} assinantes têm saída que varia | {n(len(d))} linhas; 0 removidas |",
          "| 43 | 10/11/2026 | base_assinantes_painel_rotulado | sinais de saída quase iguais ao desfecho | ler os fatores na especificação A (sem renovação desligada, prazo, carência e cancelamento no site); B só ao lado | os sinais são o mecanismo da saída, não a explicação | 0 linhas alteradas |",
          f"| 44 | 10/11/2026 | segmentos_30set | comparar segmentos com o churn sem contaminar a segmentação | aplicar o K-means de 30/09 aos cortes sem reajuste; não criar segmentação escolhida pelo churn | objetivo 3: segmentar sem a variável de saída | {n(len(d))} linhas classificadas; modelo igual ao salvo em {g(100*iguais)}% |"]
    MD.write_text("\n".join(L), encoding="utf-8")
    assert sha(PAINEL) == h0
    print(f"[saída] {MD.relative_to(RAIZ)} · {PNG.relative_to(RAIZ)} · painel inalterado")


if __name__ == "__main__":
    main()
