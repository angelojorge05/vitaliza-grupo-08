"""Base master por usuário (uma linha por conta) para a segmentação, no corte de 30/09/2026.

Espinha: usuarios.csv (64.948 contas). Tudo medido até 30/09/2026 23:59:59 (Brasília); sem rótulo de
saída. Cada fonte é resumida por user_id antes de juntar (esquerda, um-para-um, linhas conferidas).
Reaproveita as fontes e regras de src/base_assinantes.py (decisões 10, 11, 16, 23 a 25, 33 a 36).

Cada coluna recebe uma marca de uso: `agrupamento` (comportamento e perfil, pode ir ao K-means),
`descritiva` (para descrever os grupos, não para formá-los) ou `proibida` (saída/rótulo).
Saídas: dados/processados/base_master.parquet e saidas/base_master.md. Só lê os brutos (SHA-256).
"""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from base_assinantes import (BRUTOS, MAPA_SEXO, NAO_INF, PROC, CAP_RECENCIA, Fontes, fim_do_periodo, n, sha256, tabela)

RAIZ = Path(__file__).resolve().parent.parent
RELATORIO = RAIZ / "saidas" / "base_master.md"
CORTE = pd.Timestamp("2026-09-30")
FIM_DIA = CORTE + pd.Timedelta(hours=23, minutes=59, seconds=59)
AR_LIVRE = ["corrida", "caminhada", "pedal"]
VIDEO = ["funcional", "forca", "yoga", "hiit"]

# coluna -> (bloco, uso)
DIC: dict[str, tuple[str, str]] = {}


def marca(bloco: str, uso: str, *cols: str) -> None:
    for c in cols:
        DIC[c] = (bloco, uso)


def main() -> None:
    arquivos = [BRUTOS / x for x in ["assinaturas.csv", "eventos_assinatura.csv", "usuarios.csv", "pagamentos.csv",
                                     "uso_mensal.csv", "amizades.csv", "feed_posts.csv", "tickets_suporte.csv",
                                     "campanha_ago26.csv", "atividades.parquet", "onboarding.csv"]]
    hash_antes = sha256(*arquivos)
    f = Fontes()
    log: list[str] = []
    maximos: dict[str, object] = {}

    def passo(nome, antes, depois, nota=""):
        log.append(f"| {nome} | {n(antes)} | {n(depois)} | {nota} |")
        print(f"[{nome}] {n(antes)} → {n(depois)} {nota}")

    # espinha
    us = f.usuarios.copy()
    master = us[["user_id", "data_cadastro", "sexo", "uf", "canal_aquisicao", "sistema", "relogio_conectado",
                 "data_nascimento", "flag_email_repetido"]].copy()
    n_contas = len(master)
    assert master["user_id"].is_unique
    master["flag_conta_teste"] = master["user_id"].isin(f.teste)
    cad = pd.to_datetime(master["data_cadastro"], errors="coerce")
    master["flag_cadastro_apos_corte"] = cad > FIM_DIA
    master["dias_desde_cadastro"] = (CORTE - cad.dt.normalize()).dt.days.clip(lower=0)
    nasc = pd.to_datetime(master["data_nascimento"], errors="coerce")
    inval = (nasc > FIM_DIA) | (nasc < "1920-01-01") | nasc.isna()
    master["idade"] = ((FIM_DIA - nasc).dt.days / 365.25).round(1).where(~inval)
    master["flag_nascimento_invalido"] = inval
    master["sexo"] = master["sexo"].map(MAPA_SEXO).fillna(NAO_INF)
    master["sistema"] = master["sistema"].str.lower()
    master["relogio_conectado"] = master["relogio_conectado"].replace("", "nenhum")
    master["uf"] = master["uf"].replace("", NAO_INF)
    master = master.drop(columns=["data_cadastro", "data_nascimento"])
    passo("espinha: usuarios.csv", n_contas, len(master), f"{n(master['flag_conta_teste'].sum())} contas de teste marcadas")

    def juntar(nome, bloco, nota=""):
        nonlocal master
        antes = len(master)
        master = master.merge(bloco, on="user_id", how="left", validate="one_to_one")
        assert len(master) == antes, f"{nome} multiplicou linhas"
        passo(f"junção: {nome}", antes, len(master), nota)

    # assinatura (todas, inclusive cortesia/teste, que ficam marcadas)
    a = pd.read_csv(BRUTOS / "assinaturas.csv", dtype=str, keep_default_na=False)
    a["inicio_d"] = pd.to_datetime(a["inicio"], format="%Y-%m-%d")
    a["fim_d"] = pd.to_datetime(a["data_fim"].replace("", np.nan), format="%Y-%m-%d")
    assert a["user_id"].is_unique
    ativo = (a["inicio_d"] <= CORTE) & (a["fim_d"].isna() | (a["fim_d"] > CORTE))
    ex = a["fim_d"].notna() & (a["fim_d"] <= CORTE)
    a["situacao_no_corte"] = np.select([ativo, ex], ["ativo", "ex_assinante"], default="assinatura_futura")
    a["tempo_de_casa_dias"] = ((a["fim_d"].where(ex, CORTE)) - a["inicio_d"]).dt.days
    a["dias_desde_fim"] = np.where(ex, (CORTE - a["fim_d"]).dt.days, np.nan)
    a = a.rename(columns={"data_fim": "data_fim_assinatura"})
    sub = a[["user_id", "plano_atual", "canal_cobranca", "situacao_no_corte", "tempo_de_casa_dias", "dias_desde_fim",
             "data_fim_assinatura", "motivo_fim"]].copy()
    sub["plano_atual"] = sub["plano_atual"]
    # eventos até o corte
    ev = f.eventos[(f.eventos["quando"] <= FIM_DIA) & f.eventos["user_id"].isin(a["user_id"])]
    maximos["eventos"] = ev["quando"].max()
    tog = ev[ev["evento"].isin(["renovacao_automatica_desligada", "renovacao_automatica_religada"])].sort_values("quando")
    ult = tog.groupby("user_id").agg(ult_evento=("evento", "last"), quando=("quando", "last"))
    se = pd.DataFrame(index=ult.index)
    se["renovacao_desligada"] = ult["ult_evento"].eq("renovacao_automatica_desligada")
    se["dias_desde_desligamento"] = np.where(se["renovacao_desligada"], (FIM_DIA - ult["quando"]).dt.days, 0)
    se["n_renovacoes"] = ev[ev["evento"] == "renovacao"].groupby("user_id").size()
    se["n_carencia"] = ev[ev["evento"] == "periodo_carencia"].groupby("user_id").size()
    se["tem_cancelamento_web"] = ev[ev["evento"] == "cancelamento_web"].groupby("user_id").size().gt(0)
    sub = sub.merge(se.reset_index(), on="user_id", how="left")
    ativos_idx = sub["situacao_no_corte"] == "ativo"
    fim_calc = fim_do_periodo(a.set_index("user_id").loc[sub["user_id"], "inicio_d"].reset_index(drop=True), CORTE,
                              sub["plano_atual"].reset_index(drop=True))
    sub["dias_ate_fim_periodo"] = np.where(ativos_idx, (fim_calc - CORTE).dt.days, np.nan)
    # renovação e prazo só fazem sentido para quem está ativo
    for c in ["renovacao_desligada", "tem_cancelamento_web"]:
        sub[c] = sub[c].where(ativos_idx).astype("boolean")
    sub.loc[~ativos_idx, ["dias_desde_desligamento"]] = np.nan
    sub.loc[ativos_idx, "renovacao_desligada"] = sub.loc[ativos_idx, "renovacao_desligada"].fillna(False)
    sub.loc[ativos_idx, "tem_cancelamento_web"] = sub.loc[ativos_idx, "tem_cancelamento_web"].fillna(False)
    sub.loc[ativos_idx, "dias_desde_desligamento"] = sub.loc[ativos_idx, "dias_desde_desligamento"].fillna(0)
    for c in ["n_renovacoes", "n_carencia"]:
        sub[c] = sub[c].fillna(0).astype(int)
    sub["motivo_fim"] = sub["motivo_fim"].replace("", np.nan)
    sub["data_fim_assinatura"] = sub["data_fim_assinatura"].replace("", np.nan)
    juntar("assinatura e eventos", sub, f"{n(len(sub))} contas com assinatura")
    master["situacao_no_corte"] = master["situacao_no_corte"].fillna("nunca_assinou")
    master["ativo_no_corte"] = (master["situacao_no_corte"] == "ativo") & ~master["flag_conta_teste"]
    for c in ["n_renovacoes", "n_carencia"]:
        master[c] = master[c].fillna(0).astype(int)
    master["plano_atual"] = master["plano_atual"].fillna(NAO_INF)
    master["canal_cobranca"] = master["canal_cobranca"].fillna(NAO_INF)

    # onboarding
    ob = pd.read_csv(PROC / "base_conta_onboarding.csv", dtype=str, keep_default_na=False,
                     usecols=["user_id", "nivel", "dias_por_semana_num", "sem_questionario", "nivel_nao_informado",
                              "dias_por_semana_nao_informado", "objetivo_sem_resposta"])
    ob["nivel"] = ob["nivel"].replace("", NAO_INF)
    ob["dias_semana_declarado"] = pd.to_numeric(ob["dias_por_semana_num"], errors="coerce")
    for c in ["sem_questionario", "nivel_nao_informado", "dias_por_semana_nao_informado", "objetivo_sem_resposta"]:
        ob[c] = ob[c].str.lower().eq("true")
    ob = ob.rename(columns={"nivel": "nivel_declarado"}).drop(columns="dias_por_semana_num")
    juntar("onboarding", ob)
    master["nivel_declarado"] = master["nivel_declarado"].fillna(NAO_INF)
    for c in ["sem_questionario", "nivel_nao_informado", "dias_por_semana_nao_informado", "objetivo_sem_resposta"]:
        master[c] = master[c].fillna(True).astype(bool)

    # treinos
    t = f.treinos[f.treinos["inicio"] <= FIM_DIA].copy()
    maximos["treinos"] = t["inicio"].max()
    n_treinos = len(t)
    t["dias"] = (FIM_DIA.normalize() - t["inicio"].dt.normalize()).dt.days
    t["relogio"] = t["origem"] != "app"
    g30, g60, g90 = t[t["dias"] < 30], t[t["dias"] < 60], t[t["dias"] < 90]
    ct = t.groupby(["user_id", "tipo"]).size().reset_index(name="n")
    principal = ct.loc[ct.groupby("user_id")["n"].idxmax()].set_index("user_id")["tipo"]
    ft = pd.DataFrame({
        "treinos_30d": g30.groupby("user_id").size(), "treinos_60d": g60.groupby("user_id").size(),
        "treinos_90d": g90.groupby("user_id").size(), "minutos_30d": g30.groupby("user_id")["duracao_min"].sum(),
        "minutos_90d": g90.groupby("user_id")["duracao_min"].sum(), "km_90d": g90.groupby("user_id")["distancia_km"].sum(),
        "n_modalidades_90d": g90.groupby("user_id")["tipo"].nunique(),
        "pct_relogio_90d": (100 * g90.groupby("user_id")["relogio"].mean()).round(1),
        "recencia_dias": t.groupby("user_id")["dias"].min(),
        "treinos_total": t.groupby("user_id").size(), "minutos_total": t.groupby("user_id")["duracao_min"].sum(),
        "km_total": t.groupby("user_id")["distancia_km"].sum(), "n_modalidades_total": t.groupby("user_id")["tipo"].nunique(),
        "tipo_principal": principal,
        "pct_ar_livre": (100 * t["tipo"].isin(AR_LIVRE).groupby(t["user_id"]).mean()).round(1),
        "pct_video": (100 * t["tipo"].isin(VIDEO).groupby(t["user_id"]).mean()).round(1),
        "_t31_90": t[(t["dias"] >= 30) & (t["dias"] < 90)].groupby("user_id").size()})
    ft = ft.reset_index().rename(columns={"index": "user_id"})
    juntar("treinos até o corte", ft, f"{n(len(ft))} contas com treino, {n(n_treinos)} treinos")
    zeros = ["treinos_30d", "treinos_60d", "treinos_90d", "n_modalidades_90d", "treinos_total", "n_modalidades_total", "_t31_90"]
    master[zeros] = master[zeros].fillna(0).astype(int)
    for c in ["minutos_30d", "minutos_90d", "km_90d", "pct_relogio_90d", "minutos_total", "km_total", "pct_ar_livre", "pct_video"]:
        master[c] = master[c].fillna(0.0)
    master["tipo_principal"] = master["tipo_principal"].fillna("sem_treino")
    master["sem_treino_90d"] = master["treinos_90d"] == 0
    master["tem_treino"] = master["treinos_total"] > 0
    master["recencia_dias"] = master["recencia_dias"].fillna(CAP_RECENCIA).clip(upper=CAP_RECENCIA).astype(int)
    media_ant = master["_t31_90"] / 2
    master["tendencia"] = np.where(media_ant > 0, (master["treinos_30d"] / media_ant.where(media_ant > 0)).round(2), 1.0)
    master = master.drop(columns="_t31_90")

    # app
    meses3 = ["2026-07", "2026-08", "2026-09"]
    u = f.uso[f.uso["mes"].isin(meses3)]
    maximos["uso_mensal"] = u["mes"].max()
    atual = u[u["mes"] == "2026-09"].set_index("user_id")[["sessoes_app", "dias_ativos", "minutos"]]
    atual.columns = ["sessoes_app_mes", "dias_ativos_mes", "minutos_mes"]
    tres = u.groupby("user_id")[["sessoes_app", "minutos"]].sum() / 3
    tres.columns = ["sessoes_app_3m", "minutos_3m"]
    juntar("uso mensal", atual.join(tres, how="outer").reset_index().rename(columns={"index": "user_id"}))
    for c in ["sessoes_app_mes", "dias_ativos_mes", "minutos_mes", "sessoes_app_3m", "minutos_3m"]:
        master[c] = master[c].fillna(0.0)

    # pagamentos
    p = f.pag[f.pag["dt_brt"] <= FIM_DIA]
    maximos["pagamentos"] = p["dt_brt"].max()
    ap, rec = p[p["status"] == "aprovado"], p[p["status"] == "recusado"]
    rec90 = rec[rec["dt_brt"] > FIM_DIA - pd.Timedelta(days=90)]
    fp = pd.DataFrame({
        "pg_aprovados": ap.groupby("user_id").size(), "pg_valor_medio": ap.groupby("user_id")["valor"].mean().round(2),
        "pg_metodo_principal": ap.groupby("user_id")["metodo"].agg(lambda s: s.mode().iat[0]),
        "pg_recusas": rec.groupby("user_id").size(), "pg_recusas_90d": rec90.groupby("user_id").size(),
        "pg_estornos": p[p["status"].isin(["estornado", "chargeback"])].groupby("user_id").size()})
    juntar("pagamentos", fp.reset_index().rename(columns={"index": "user_id"}), f"{n(len(fp))} contas com cobrança")
    for c in ["pg_aprovados", "pg_recusas", "pg_recusas_90d", "pg_estornos"]:
        master[c] = master[c].fillna(0).astype(int)
    master["pg_valor_medio"] = master["pg_valor_medio"].fillna(0.0)
    master["pg_metodo_principal"] = master["pg_metodo_principal"].fillna(NAO_INF)
    den = (master["pg_recusas"] + master["pg_aprovados"]).where((master["pg_recusas"] + master["pg_aprovados"]) > 0)
    master["pg_pct_recusa"] = (100 * master["pg_recusas"] / den).round(1).fillna(0.0)

    # social
    am = f.amizades[f.amizades["desde"] <= FIM_DIA]
    maximos["amizades"] = am["desde"].max()
    po = f.posts[f.posts["dt"] <= FIM_DIA]
    maximos["posts"] = po["dt"].max()
    po90 = po[po["dt"] > FIM_DIA - pd.Timedelta(days=90)]
    so = pd.DataFrame({"n_seguindo": am.groupby("seguidor_id").size(), "n_seguidores": am.groupby("seguido_id").size(),
                       "n_posts": po.groupby("user_id").size(), "n_posts_90d": po90.groupby("user_id").size()})
    so = so[so.index.isin(master["user_id"])]
    juntar("social", so.reset_index().rename(columns={"index": "user_id"}))
    for c in ["n_seguindo", "n_seguidores", "n_posts", "n_posts_90d"]:
        master[c] = master[c].fillna(0).astype(int)

    # suporte
    tk = f.tickets[f.tickets["dt"] <= FIM_DIA]
    maximos["tickets"] = tk["dt"].max()
    tk90 = tk[tk["dt"] > FIM_DIA - pd.Timedelta(days=90)]
    su = pd.DataFrame({"n_tickets": tk.groupby("user_id").size(), "n_tickets_90d": tk90.groupby("user_id").size(),
                       "ticket_categoria_principal": tk.groupby("user_id")["categoria_atendente"].agg(
                           lambda s: s.mode().iat[0] if s.notna().any() else NAO_INF)})
    juntar("suporte", su.reset_index().rename(columns={"index": "user_id"}))
    for c in ["n_tickets", "n_tickets_90d"]:
        master[c] = master[c].fillna(0).astype(int)
    master["ticket_categoria_principal"] = master["ticket_categoria_principal"].fillna(NAO_INF)

    # campanha
    c = f.campanha[["user_id", "grupo", "abriu_push", "abriu_email", "clicou"]].copy()
    for col in ["abriu_push", "abriu_email", "clicou"]:
        c[col] = c[col].str.lower().eq("true")
    c = c.rename(columns={"grupo": "grupo_campanha", "abriu_push": "camp_abriu_push", "abriu_email": "camp_abriu_email",
                          "clicou": "camp_clicou"})
    juntar("campanha de 10/08", c, f"{n(master['user_id'].isin(c['user_id']).sum())} sorteados")
    master["grupo_campanha"] = master["grupo_campanha"].fillna("fora_da_campanha")
    for col in ["camp_abriu_push", "camp_abriu_email", "camp_clicou"]:
        master[col] = master[col].fillna(False).astype(bool)

    # marcas de uso por coluna
    marca("Identificação", "descritiva", "user_id")
    marca("Perfil", "agrupamento", "idade", "sexo", "uf", "canal_aquisicao", "sistema", "relogio_conectado", "dias_desde_cadastro")
    marca("Perfil", "descritiva", "flag_nascimento_invalido", "flag_cadastro_apos_corte", "flag_email_repetido", "flag_conta_teste")
    marca("Assinatura", "descritiva", "situacao_no_corte", "ativo_no_corte", "plano_atual", "canal_cobranca", "tempo_de_casa_dias")
    marca("Assinatura (sinais de saída)", "descritiva", "renovacao_desligada", "dias_desde_desligamento", "tem_cancelamento_web",
          "dias_ate_fim_periodo", "n_carencia")
    marca("Assinatura", "agrupamento", "n_renovacoes")
    marca("Assinatura (saída já ocorrida)", "proibida", "dias_desde_fim", "data_fim_assinatura", "motivo_fim")
    marca("Onboarding", "agrupamento", "nivel_declarado", "dias_semana_declarado")
    marca("Onboarding", "descritiva", "sem_questionario", "nivel_nao_informado", "dias_por_semana_nao_informado", "objetivo_sem_resposta")
    marca("Treinos", "agrupamento", "treinos_30d", "treinos_60d", "treinos_90d", "minutos_30d", "minutos_90d", "km_90d",
          "n_modalidades_90d", "pct_relogio_90d", "recencia_dias", "treinos_total", "minutos_total", "km_total",
          "n_modalidades_total", "tipo_principal", "pct_ar_livre", "pct_video", "tendencia")
    marca("Treinos", "descritiva", "sem_treino_90d", "tem_treino")
    marca("App", "agrupamento", "sessoes_app_mes", "dias_ativos_mes", "minutos_mes", "sessoes_app_3m", "minutos_3m")
    marca("Pagamentos", "agrupamento", "pg_aprovados", "pg_recusas", "pg_recusas_90d", "pg_estornos", "pg_pct_recusa", "pg_valor_medio",
          "pg_metodo_principal")
    marca("Social", "agrupamento", "n_seguindo", "n_seguidores", "n_posts", "n_posts_90d")
    marca("Suporte", "agrupamento", "n_tickets", "n_tickets_90d", "ticket_categoria_principal")
    marca("Campanha", "descritiva", "grupo_campanha", "camp_abriu_push", "camp_abriu_email", "camp_clicou")
    sem_marca = [c_ for c_ in master.columns if c_ not in DIC]
    assert not sem_marca, f"colunas sem marca de uso: {sem_marca}"
    master = master[list(DIC)]  # ordem por bloco

    # conferências
    PROC.mkdir(parents=True, exist_ok=True)
    master.to_parquet(PROC / "base_master.parquet", index=False)
    problemas = []
    if len(master) != n_contas or not master["user_id"].is_unique:
        problemas.append("linhas ≠ contas ou user_id repetido")
    n_ativos = int(master["ativo_no_corte"].sum())
    if n_ativos != 14753:
        problemas.append(f"ativos {n_ativos} ≠ 14.753")
    soma_t = int(master["treinos_total"].sum())
    if soma_t != n_treinos:
        problemas.append(f"treinos por conta {soma_t} ≠ treinos usados {n_treinos}")
    ct_path = PROC / "contas_treinos.parquet"
    dif_ct = None
    if ct_path.exists():
        cc = pd.read_parquet(ct_path, columns=["user_id", "treinos_sem_dup"]).merge(master[["user_id", "treinos_total"]], on="user_id")
        dif_ct = int((cc["treinos_sem_dup"] != cc["treinos_total"]).sum())
        if dif_ct:
            problemas.append(f"{dif_ct} contas com treinos diferentes de contas_treinos")
    ba_path = PROC / "base_assinantes_2026-09-30.parquet"
    dif_ba = {}
    if ba_path.exists():
        ba = pd.read_parquet(ba_path)
        mm = master[master["ativo_no_corte"]].merge(ba, on="user_id", suffixes=("", "_ba"))
        if len(mm) != len(ba):
            problemas.append(f"ativos em comum com base_assinantes: {len(mm)} de {len(ba)}")
        for col in ["treinos_30d", "treinos_90d", "minutos_30d", "recencia_dias", "tendencia", "renovacao_desligada",
                    "dias_ate_fim_periodo", "pg_aprovados", "pg_recusas", "n_seguidores", "n_posts", "n_tickets",
                    "sessoes_app_mes", "idade", "tenure_dias", "grupo_campanha"]:
            if col == "tenure_dias":
                a_, b_ = mm["tempo_de_casa_dias"], mm["tenure_dias"]
            elif col + "_ba" in mm.columns:
                a_, b_ = mm[col], mm[col + "_ba"]
            else:  # coluna só existe na base_assinantes com o mesmo nome (sem sufixo)
                a_, b_ = mm[col], mm[col]
            iguais = (a_.astype(object).where(a_.notna(), None) == b_.astype(object).where(b_.notna(), None)) | (a_.isna() & b_.isna())
            dif_ba[col] = int((~iguais).sum())
        if any(dif_ba.values()):
            problemas.append(f"diferenças com base_assinantes: { {k: v for k, v in dif_ba.items() if v} }")
    for fonte, mx in maximos.items():
        ok = (pd.Period(mx, "M") <= pd.Period("2026-09", "M")) if fonte == "uso_mensal" else (pd.Timestamp(mx) <= FIM_DIA)
        if not ok:
            problemas.append(f"{fonte} usa {mx}")
    nulos = master.select_dtypes("number").isna().sum()
    nulos = nulos[nulos > 0]
    print(f"[checagens] " + ("OK" if not problemas else "; ".join(problemas)))
    print(f"[saída] base_master.parquet: {n(len(master))} linhas × {master.shape[1]} colunas")

    sit = master["situacao_no_corte"].value_counts()
    uso = pd.Series({k: v[1] for k, v in DIC.items()}).value_counts()
    estado = "inalterados" if sha256(*arquivos) == hash_antes else "ALTERADOS"
    out = ["# Base master por usuário (corte de 30/09/2026)\n",
           f"Gerado por `src/base_master.py`. Só leitura dos brutos (SHA-256 conjunto `{hash_antes[:16]}…`, {estado}). **{n(len(master))} linhas × {master.shape[1]} colunas**, uma por conta, tudo medido até 30/09/2026 23:59:59 (Brasília), sem rótulo de saída. Arquivo `dados/processados/base_master.parquet` (fora do Git).\n",
           "## 1. Quem está na base\n",
           tabela(pd.DataFrame([[k, n(v)] for k, v in sit.items()] + [["ativos no corte (sem teste)", n(n_ativos)],
                                                                      ["contas de teste (marcadas, mantidas)", n(master['flag_conta_teste'].sum())]],
                                columns=["situação no corte", "contas"])) + "\n",
           "Segmentação: filtrar `ativo_no_corte` (14.753). `flag_conta_teste` e `flag_email_repetido` ficam como marcas, sem remover (decisão 22 e pendência dos e-mails).\n",
           "## 2. Checagens\n",
           f"- Linhas = contas de `usuarios.csv` ({n(n_contas)}), um `user_id` por linha: {'✔' if len(master) == n_contas and master['user_id'].is_unique else '✘'}.",
           f"- Ativos no corte = 14.753 (série de churn): {'✔' if n_ativos == 14753 else '✘'}.",
           f"- Soma dos treinos por conta = treinos usados ({n(n_treinos)}): {'✔' if soma_t == n_treinos else '✘'}; contas com treino diferente de `contas_treinos.treinos_sem_dup`: {n(dif_ct) if dif_ct is not None else 'n/d'}.",
           f"- Mesmos valores da `base_assinantes` de 30/09 para os 14.753 ativos (16 colunas comparadas): diferenças {sum(dif_ba.values()) if dif_ba else 'n/d'}.",
           f"- Nenhuma fonte passa do corte: {'✔' if not any('usa' in p_ for p_ in problemas) else '✘'} (máximos: " + "; ".join(f"{k} {str(v)[:16]}" for k, v in maximos.items()) + ").",
           "- Nulos que sobram nas numéricas: " + (", ".join(f"`{k}` {n(v)}" for k, v in nulos.items()) if len(nulos) else "nenhum") + " (idade com marca; colunas de assinatura só se aplicam a quem tem assinatura ou está ativo).\n",
           "## 3. Linhas antes e depois de cada passo\n",
           "| passo | linhas antes | linhas depois | observação |", "|---|---|---|---|", *log, "",
           "## 4. Dicionário e marca de uso para a segmentação\n",
           "`agrupamento` = pode formar os grupos (comportamento e perfil); `descritiva` = serve para descrever os grupos depois, não para formá-los; `proibida` = saída/rótulo, nunca no agrupamento. Os sinais de intenção de saída (renovação desligada, cancelamento no site, carência, prazo até o fim do período) ficam como descritivos para os grupos não virarem um preditor de churn disfarçado.\n",
           tabela(pd.DataFrame([[c_, b_, u_] for c_, (b_, u_) in DIC.items()], columns=["coluna", "bloco", "uso"])) + "\n",
           f"Colunas por uso: " + ", ".join(f"{k} {v}" for k, v in uso.items()) + ".\n",
           "## 5. Regras e armadilhas\n",
           "- Treinos de `atividades_limpa_v2` (decisões 10, 11, 23 a 25; só 2026); pagamentos sem duplicatas aprovadas (decisão 16); fuso em Brasília (decisão 13).",
           "- Vazios: contagens = 0; recência de quem não treinou = 90 (teto) com `sem_treino_90d`; tendência sem base = 1,0; categóricas = `nao_informado`; `tipo_principal` = `sem_treino`; idade NA com marca.",
           "- Quem nunca assinou (freemium) tem plano e canal `nao_informado` e nulos nas colunas de assinatura; o comportamento dele é bem diferente do de um assinante, e a segmentação do case é sobre os ativos.",
           "- `ex_assinante` e as colunas de fim são saída já ocorrida: por isso `proibida` para o agrupamento.",
           "- `grupo_campanha` descreve a campanha de 10/08; não deve formar grupos, porque o sorteio é aleatório.\n",
           "## 6. Decisões propostas (formato do `decisoes.md`, não gravadas)\n",
           "| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |",
           "|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|",
           f"| 37 | 09/11/2026 | usuarios.csv + demais fontes | base única por usuário para a segmentação | base master de uma linha por conta no corte de 30/09 (64.948 contas; 14.753 ativos), com a marca `ativo_no_corte` e sem rótulo de saída; teste e e-mail repetido só marcados | segmentar sem usar a variável de saída (objetivo 3); manter todas as contas deixa olhar também quem nunca pagou | {n(n_contas)} → {n(len(master))} linhas; {master.shape[1]} colunas |",
           f"| 38 | 09/11/2026 | base_master | colunas ligadas à saída podem contaminar o agrupamento | cada coluna ganha a marca `agrupamento`, `descritiva` ou `proibida`; sinais de intenção de saída e a campanha só descrevem | evita um agrupamento que seja um preditor de churn disfarçado | {int(uso.get('agrupamento', 0))} para agrupamento, {int(uso.get('descritiva', 0))} descritivas, {int(uso.get('proibida', 0))} proibidas |",
           f"\n---\nConferência: brutos {estado}."]
    RELATORIO.write_text("\n".join(out), encoding="utf-8")
    print(f"brutos {estado} · escrito: {RELATORIO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
