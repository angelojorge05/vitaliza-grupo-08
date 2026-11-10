"""Base de assinantes ativos em um corte, com rótulo de saída em 60 dias (objetivo 4 do case).

Cortes: 30/04, 31/05 (treino), 30/06 (validação) e 30/09/2026 (aplicação, sem rótulo: a saída até
29/11/2026 ainda não aconteceu). Uma linha por assinante ativo no corte, sem contas de teste/cortesia.

Tudo é medido ATÉ o corte (Brasília). Cada fonte é resumida por user_id antes de juntar (junção esquerda,
um-para-um, com as linhas conferidas). O rótulo `saiu_60d` = data_fim entre corte+1 e corte+60 dias e nunca
entra nas variáveis; `rotulo_motivo_fim` é só descrição do rótulo, não variável.

Saídas: dados/processados/base_assinantes_<corte>.parquet e saidas/base_assinantes.md.
Só lê os brutos (SHA-256 antes e depois).
"""

import hashlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from utils import contas_de_teste, para_brasilia

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos"
PROC = RAIZ / "dados" / "processados"
RELATORIO = RAIZ / "saidas" / "base_assinantes.md"
CORTES = [("2026-04-30", "treino"), ("2026-05-31", "treino"), ("2026-06-30", "validação"), ("2026-09-30", "aplicação")]
HORIZONTE = 60
NAO_INF = "nao_informado"
MAPA_SEXO = {"F": "F", "Fem": "F", "feminino": "F", "M": "M", "Masc": "M", "masculino": "M"}
CHAVE_DEDUP = ["user_id", "dt_brt", "valor", "metodo", "status", "tentativa"]
CAP_RECENCIA = 90
CHURN_ATIVOS = {"2026-04-30": 14119, "2026-05-31": 14102, "2026-06-30": 14059, "2026-09-30": 14753}  # série de churn_mensal


def sha256(*caminhos: Path) -> str:
    h = hashlib.sha256()
    for c in caminhos:
        with open(c, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
    return h.hexdigest()


def n(x) -> str:
    return f"{int(x):,}".replace(",", ".")


def tabela(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    return "\n".join([cab, sep, *("| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False))])


def fim_do_periodo(inicio: pd.Series, corte: pd.Timestamp, plano: pd.Series) -> pd.Series:
    """Próximo fim de período pago depois do corte, no padrão medido em data_fim.

    mensal: inicio + 30*k dias; anual: aniversário (inicio + k anos).
    """
    dias = (corte - inicio).dt.days
    k_m = dias // 30 + 1
    fim_m = inicio + pd.to_timedelta(30 * k_m, unit="D")
    k_a = (corte.year - inicio.dt.year).clip(lower=0)

    def aniversario(k):
        alvo = inicio.dt.to_period("M") + (12 * k)
        dia = np.minimum(inicio.dt.day, alvo.dt.days_in_month)
        return alvo.dt.to_timestamp() + pd.to_timedelta(dia - 1, unit="D")

    fim_a = aniversario(k_a)
    fim_a = fim_a.where(fim_a > corte, aniversario(k_a + 1))
    return fim_m.where(plano == "mensal", fim_a)


class Fontes:
    """Lê e prepara cada fonte uma vez; os cortes só filtram por data."""

    def __init__(self) -> None:
        self.teste = contas_de_teste()
        a = pd.read_csv(BRUTOS / "assinaturas.csv", dtype=str, keep_default_na=False)
        self.n_assin0 = len(a)
        a = a[(a["plano_atual"] != "cortesia") & ~a["user_id"].isin(self.teste)].copy()
        self.n_assin = len(a)
        a["inicio_d"] = pd.to_datetime(a["inicio"], format="%Y-%m-%d")
        a["fim_d"] = pd.to_datetime(a["data_fim"].replace("", np.nan), format="%Y-%m-%d")
        self.assin = a

        ev = pd.read_csv(BRUTOS / "eventos_assinatura.csv", dtype=str, keep_default_na=False)
        ev["quando"] = para_brasilia(ev["data_hora"])
        self.eventos = ev.dropna(subset=["quando"])

        us = pd.read_csv(BRUTOS / "usuarios.csv", dtype=str, keep_default_na=False)
        us["email_norm"] = us["email"].str.strip().str.lower()
        us["flag_email_repetido"] = us["email_norm"].duplicated(keep=False)
        self.usuarios = us

        ob = pd.read_csv(PROC / "base_conta_onboarding.csv", dtype=str, keep_default_na=False,
                         usecols=["user_id", "nivel", "dias_por_semana_num", "sem_questionario",
                                  "nivel_nao_informado", "dias_por_semana_nao_informado", "objetivo_sem_resposta"])
        self.onboarding = ob

        v2 = PROC / "atividades_limpa_v2.parquet"
        if not v2.exists():
            subprocess.run([sys.executable, str(RAIZ / "src" / "limpar_outliers_atividades.py")], check=True)
        self.treinos = pd.read_parquet(v2, columns=["atividade_id", "user_id", "inicio", "tipo", "duracao_min",
                                                    "distancia_km", "origem"])
        self.treinos["inicio"] = pd.to_datetime(self.treinos["inicio"])

        self.uso = pd.read_csv(BRUTOS / "uso_mensal.csv", dtype={"user_id": str, "mes": str})

        p = pd.read_csv(BRUTOS / "pagamentos.csv", dtype=str, keep_default_na=False)
        p["valor"] = pd.to_numeric(p["valor"].str.replace("R$", "", regex=False).str.strip()
                                   .str.replace(",", ".", regex=False), errors="coerce")
        p["dt_brt"] = para_brasilia(p["data_hora"])
        self.pag_brutos = len(p)
        dup = p["status"].eq("aprovado") & p.duplicated(subset=CHAVE_DEDUP, keep="first")
        self.pag_dup = int(dup.sum())
        self.pag = p[~dup].copy()

        am = pd.read_csv(BRUTOS / "amizades.csv", dtype=str)
        am["desde"] = pd.to_datetime(am["desde"], errors="coerce")
        self.amizades = am
        fp = pd.read_csv(BRUTOS / "feed_posts.csv", dtype=str, usecols=["user_id", "data_hora"])
        fp["dt"] = para_brasilia(fp["data_hora"])
        self.posts = fp.dropna(subset=["dt"])
        tk = pd.read_csv(BRUTOS / "tickets_suporte.csv", dtype=str, usecols=["user_id", "aberto_em", "categoria_atendente"])
        tk["dt"] = para_brasilia(tk["aberto_em"])
        self.tickets = tk.dropna(subset=["dt"])
        self.campanha = pd.read_csv(BRUTOS / "campanha_ago26.csv", dtype=str, keep_default_na=False)


def construir(f: Fontes, corte_txt: str, papel: str, log: list[str]) -> tuple[pd.DataFrame, dict]:
    corte = pd.Timestamp(corte_txt)
    fim_dia = corte + pd.Timedelta(hours=23, minutes=59, seconds=59)
    janela_fim = corte + pd.Timedelta(days=HORIZONTE)
    info: dict = {"corte": corte_txt, "papel": papel, "janela_fim": janela_fim.date().isoformat(), "max_datas": {}}
    L = log.append

    def passo(nome: str, antes: int, depois: int, nota: str = "") -> None:
        L(f"| {nome} | {n(antes)} | {n(depois)} | {nota} |")

    # espinha
    a = f.assin
    ativo = (a["inicio_d"] <= corte) & (a["fim_d"].isna() | (a["fim_d"] > corte))
    esp = a.loc[ativo, ["user_id", "assinatura_id", "plano_atual", "canal_cobranca", "inicio_d", "fim_d", "motivo_fim"]].copy()
    passo("assinaturas sem cortesia/teste", f.n_assin0, f.n_assin, "decisão 1")
    passo("ativas no corte", f.n_assin, len(esp), f"série de churn: {n(CHURN_ATIVOS[corte_txt])}")
    info["ativos"] = len(esp)
    info["ativos_serie"] = CHURN_ATIVOS[corte_txt]
    assert esp["user_id"].is_unique

    # rótulo (só cortes passados)
    if papel != "aplicação":
        esp["saiu_60d"] = esp["fim_d"].notna() & (esp["fim_d"] <= janela_fim)
        esp["rotulo_motivo_fim"] = esp["motivo_fim"].where(esp["saiu_60d"], "")
        info["saiu"] = int(esp["saiu_60d"].sum())
        info["taxa"] = 100 * esp["saiu_60d"].mean()
        direto = int(((a["inicio_d"] <= corte) & (a["fim_d"] > corte) & (a["fim_d"] <= janela_fim)).sum())
        info["saiu_direto"] = direto
    esp = esp.drop(columns=["fim_d", "motivo_fim"])
    esp["corte"] = corte_txt
    esp["tenure_dias"] = (corte - esp["inicio_d"]).dt.days

    base = esp
    n_esp = len(base)

    def juntar(nome: str, bloco: pd.DataFrame, nota: str = "") -> None:
        nonlocal base
        antes = len(base)
        base = base.merge(bloco, on="user_id", how="left", validate="one_to_one")
        assert len(base) == antes, f"{nome} multiplicou linhas"
        passo(f"junção: {nome}", antes, len(base), nota)

    # assinatura pelos eventos (situação no corte, sem usar o retrato de 01/10)
    ev = f.eventos[(f.eventos["quando"] <= fim_dia) & f.eventos["user_id"].isin(base["user_id"])]
    info["max_datas"]["eventos"] = ev["quando"].max()
    tog = ev[ev["evento"].isin(["renovacao_automatica_desligada", "renovacao_automatica_religada"])].sort_values("quando")
    ult = tog.groupby("user_id").agg(ult_evento=("evento", "last"), quando=("quando", "last"))
    sit = pd.DataFrame(index=ult.index)
    sit["renovacao_desligada"] = ult["ult_evento"].eq("renovacao_automatica_desligada")
    sit["dias_desde_desligamento"] = np.where(sit["renovacao_desligada"], (fim_dia - ult["quando"]).dt.days, 0)
    sit["n_renovacoes"] = ev[ev["evento"] == "renovacao"].groupby("user_id").size()
    sit["n_carencia"] = ev[ev["evento"] == "periodo_carencia"].groupby("user_id").size()
    sit["tem_cancelamento_web"] = ev[ev["evento"] == "cancelamento_web"].groupby("user_id").size().gt(0)
    sit = sit.reset_index()
    juntar("situação pelos eventos", sit, f"{n(int(sit['renovacao_desligada'].sum()))} com renovação desligada")
    for c in ["renovacao_desligada", "tem_cancelamento_web"]:
        base[c] = base[c].fillna(False).astype(bool)
    for c in ["dias_desde_desligamento", "n_renovacoes", "n_carencia"]:
        base[c] = base[c].fillna(0).astype(int)
    fim_calc = fim_do_periodo(base["inicio_d"], corte, base["plano_atual"])
    base["dias_ate_fim_periodo"] = (fim_calc - corte).dt.days
    if papel != "aplicação":
        saiu = base["saiu_60d"]
        fim_real = f.assin.set_index("user_id").loc[base.loc[saiu, "user_id"], "fim_d"].values
        calc = fim_calc[saiu]
        segundo = calc + pd.Timedelta(days=30)  # mensal que renova uma vez e sai no fim do período seguinte
        mensal = base.loc[saiu, "plano_atual"] == "mensal"
        bate = (fim_real == calc.values) | (mensal.values & (fim_real == segundo.values))
        info["renov_bate"] = int(bate.sum())
        info["renov_n"] = int(saiu.sum())

    # perfil
    us = f.usuarios[["user_id", "data_nascimento", "sexo", "uf", "canal_aquisicao", "sistema", "relogio_conectado",
                     "flag_email_repetido"]].copy()
    nasc = pd.to_datetime(us["data_nascimento"], errors="coerce")
    inval = (nasc > corte) | (nasc < "1920-01-01") | nasc.isna()
    us["idade"] = ((corte - nasc).dt.days / 365.25).round(1).where(~inval)
    us["flag_nascimento_invalido"] = inval
    us["sexo"] = us["sexo"].map(MAPA_SEXO).fillna(NAO_INF)
    us["sistema"] = us["sistema"].str.lower()
    us["relogio_conectado"] = us["relogio_conectado"].replace("", "nenhum")
    us["uf"] = us["uf"].replace("", NAO_INF)
    us = us.drop(columns="data_nascimento")
    juntar("perfil (usuarios)", us[us["user_id"].isin(base["user_id"])])

    # onboarding
    ob = f.onboarding.copy()
    ob["nivel"] = ob["nivel"].replace("", NAO_INF)
    ob["dias_semana_declarado"] = pd.to_numeric(ob["dias_por_semana_num"], errors="coerce")
    for c in ["sem_questionario", "nivel_nao_informado", "dias_por_semana_nao_informado", "objetivo_sem_resposta"]:
        ob[c] = ob[c].str.lower().eq("true")
    ob = ob.rename(columns={"nivel": "nivel_declarado"}).drop(columns="dias_por_semana_num")
    juntar("onboarding", ob[ob["user_id"].isin(base["user_id"])])
    base["nivel_declarado"] = base["nivel_declarado"].fillna(NAO_INF)
    base["sem_questionario"] = base["sem_questionario"].fillna(True).astype(bool)
    for c in ["nivel_nao_informado", "dias_por_semana_nao_informado", "objetivo_sem_resposta"]:
        base[c] = base[c].fillna(True).astype(bool)

    # treinos (resumidos por user_id; decisões 10, 11, 23, 24 e 25 já aplicadas em atividades_limpa_v2)
    t = f.treinos[(f.treinos["inicio"] <= fim_dia) & f.treinos["user_id"].isin(base["user_id"])].copy()
    info["max_datas"]["treinos"] = t["inicio"].max()
    t["dias"] = (fim_dia.normalize() - t["inicio"].dt.normalize()).dt.days
    t["relogio"] = t["origem"] != "app"
    g30, g60, g90 = t[t["dias"] < 30], t[t["dias"] < 60], t[t["dias"] < 90]
    g31_90 = t[(t["dias"] >= 30) & (t["dias"] < 90)]
    ft = pd.DataFrame({
        "treinos_30d": g30.groupby("user_id").size(), "treinos_60d": g60.groupby("user_id").size(),
        "treinos_90d": g90.groupby("user_id").size(), "minutos_30d": g30.groupby("user_id")["duracao_min"].sum(),
        "minutos_90d": g90.groupby("user_id")["duracao_min"].sum(), "km_90d": g90.groupby("user_id")["distancia_km"].sum(),
        "n_modalidades_90d": g90.groupby("user_id")["tipo"].nunique(),
        "pct_relogio_90d": (100 * g90.groupby("user_id")["relogio"].mean()).round(1),
        "recencia_dias": t.groupby("user_id")["dias"].min(), "treinos_total": t.groupby("user_id").size(),
        "_t31_90": g31_90.groupby("user_id").size()})
    ft = ft.reset_index().rename(columns={"index": "user_id"})
    juntar("treinos até o corte", ft, f"{n(len(ft))} contas com treino")
    zeros = ["treinos_30d", "treinos_60d", "treinos_90d", "n_modalidades_90d", "treinos_total", "_t31_90"]
    base[zeros] = base[zeros].fillna(0).astype(int)
    for c in ["minutos_30d", "minutos_90d", "km_90d", "pct_relogio_90d"]:
        base[c] = base[c].fillna(0.0)
    base["sem_treino_90d"] = base["treinos_90d"] == 0
    base["recencia_dias"] = base["recencia_dias"].fillna(CAP_RECENCIA).clip(upper=CAP_RECENCIA).astype(int)
    media_ant = base["_t31_90"] / 2
    base["tendencia"] = np.where(media_ant > 0, (base["treinos_30d"] / media_ant.where(media_ant > 0)).round(2), 1.0)
    base = base.drop(columns="_t31_90")

    # app (uso_mensal, regime com zeros explícitos em 2026)
    mes = corte.strftime("%Y-%m")
    meses3 = [str(p) for p in pd.period_range(end=pd.Period(mes), periods=3, freq="M")]
    u = f.uso[f.uso["mes"].isin(meses3) & f.uso["user_id"].isin(base["user_id"])]
    info["max_datas"]["uso_mensal"] = u["mes"].max()
    atual = u[u["mes"] == mes].set_index("user_id")[["sessoes_app", "dias_ativos", "minutos"]]
    atual.columns = ["sessoes_app_mes", "dias_ativos_mes", "minutos_mes"]
    tres = u.groupby("user_id")[["sessoes_app", "minutos"]].sum() / 3
    tres.columns = ["sessoes_app_3m", "minutos_3m"]
    juntar("uso mensal", atual.join(tres, how="outer").reset_index().rename(columns={"index": "user_id"}))
    for c in ["sessoes_app_mes", "dias_ativos_mes", "minutos_mes", "sessoes_app_3m", "minutos_3m"]:
        base[c] = base[c].fillna(0.0)

    # pagamentos (dedup decisão 16)
    p = f.pag[(f.pag["dt_brt"] <= fim_dia) & f.pag["user_id"].isin(base["user_id"])]
    info["max_datas"]["pagamentos"] = p["dt_brt"].max()
    ap, rec = p[p["status"] == "aprovado"], p[p["status"] == "recusado"]
    rec90 = rec[rec["dt_brt"] > fim_dia - pd.Timedelta(days=90)]
    fp = pd.DataFrame({
        "pg_aprovados": ap.groupby("user_id").size(), "pg_valor_medio": ap.groupby("user_id")["valor"].mean().round(2),
        "pg_metodo_principal": ap.groupby("user_id")["metodo"].agg(lambda s: s.mode().iat[0]),
        "pg_recusas": rec.groupby("user_id").size(), "pg_recusas_90d": rec90.groupby("user_id").size(),
        "pg_estornos": p[p["status"].isin(["estornado", "chargeback"])].groupby("user_id").size()})
    fp = fp.reset_index().rename(columns={"index": "user_id"})
    juntar("pagamentos", fp, f"{n(len(fp))} contas com cobrança")
    for c in ["pg_aprovados", "pg_recusas", "pg_recusas_90d", "pg_estornos"]:
        base[c] = base[c].fillna(0).astype(int)
    base["pg_valor_medio"] = base["pg_valor_medio"].fillna(0.0)
    base["pg_metodo_principal"] = base["pg_metodo_principal"].fillna(NAO_INF)
    base["pg_pct_recusa"] = (100 * base["pg_recusas"] / (base["pg_recusas"] + base["pg_aprovados"]).where(
        (base["pg_recusas"] + base["pg_aprovados"]) > 0)).round(1).fillna(0.0)

    # social
    am = f.amizades[f.amizades["desde"] <= fim_dia]
    info["max_datas"]["amizades"] = am["desde"].max()
    po = f.posts[(f.posts["dt"] <= fim_dia) & f.posts["user_id"].isin(base["user_id"])]
    info["max_datas"]["posts"] = po["dt"].max()
    po90 = po[po["dt"] > fim_dia - pd.Timedelta(days=90)]
    so = pd.DataFrame({"n_seguindo": am.groupby("seguidor_id").size(), "n_seguidores": am.groupby("seguido_id").size(),
                       "n_posts": po.groupby("user_id").size(), "n_posts_90d": po90.groupby("user_id").size()})
    so = so[so.index.isin(base["user_id"])].reset_index().rename(columns={"index": "user_id"})
    juntar("social", so)
    for c in ["n_seguindo", "n_seguidores", "n_posts", "n_posts_90d"]:
        base[c] = base[c].fillna(0).astype(int)

    # suporte
    tk = f.tickets[(f.tickets["dt"] <= fim_dia) & f.tickets["user_id"].isin(base["user_id"])]
    info["max_datas"]["tickets"] = tk["dt"].max()
    tk90 = tk[tk["dt"] > fim_dia - pd.Timedelta(days=90)]
    su = pd.DataFrame({"n_tickets": tk.groupby("user_id").size(), "n_tickets_90d": tk90.groupby("user_id").size(),
                       "ticket_categoria_principal": tk.groupby("user_id")["categoria_atendente"].agg(
                           lambda s: s.mode().iat[0] if s.notna().any() else NAO_INF)})
    juntar("suporte", su.reset_index().rename(columns={"index": "user_id"}))
    for c in ["n_tickets", "n_tickets_90d"]:
        base[c] = base[c].fillna(0).astype(int)
    base["ticket_categoria_principal"] = base["ticket_categoria_principal"].fillna(NAO_INF)

    # campanha (só existe como informação depois de 10/08/2026)
    if corte >= pd.Timestamp("2026-08-10"):
        c = f.campanha[["user_id", "grupo", "abriu_push", "abriu_email", "clicou"]].copy()
        for col in ["abriu_push", "abriu_email", "clicou"]:
            c[col] = c[col].str.lower().eq("true")
        c = c.rename(columns={"grupo": "grupo_campanha", "abriu_push": "camp_abriu_push",
                              "abriu_email": "camp_abriu_email", "clicou": "camp_clicou"})
        juntar("campanha de 10/08", c[c["user_id"].isin(base["user_id"])],
               f"{n(base['user_id'].isin(c['user_id']).sum())} sorteados entre os ativos")
        base["grupo_campanha"] = base["grupo_campanha"].fillna("fora_da_campanha")
        for col in ["camp_abriu_push", "camp_abriu_email", "camp_clicou"]:
            base[col] = base[col].fillna(False).astype(bool)
        info["campanha_fora"] = int((base["grupo_campanha"] == "fora_da_campanha").sum())
    info["janela_inclui_campanha"] = bool(janela_fim >= pd.Timestamp("2026-08-10") and corte < pd.Timestamp("2026-08-10"))

    base = base.rename(columns={"inicio_d": "inicio"})
    assert len(base) == n_esp and base["user_id"].is_unique
    info["linhas"] = len(base)
    info["colunas"] = base.shape[1]
    nulos = base.select_dtypes("number").isna().sum()
    info["nulos_idade"] = int(nulos.get("idade", 0))
    info["nulos_outros"] = int(nulos.drop(["idade", "dias_semana_declarado"], errors="ignore").sum())
    info["nulos_dias"] = int(nulos.get("dias_semana_declarado", 0))
    PROC.mkdir(parents=True, exist_ok=True)
    base.to_parquet(PROC / f"base_assinantes_{corte_txt}.parquet", index=False)
    print(f"[{corte_txt}] {papel}: {n(len(base))} linhas × {base.shape[1]} colunas · ativos da série {n(CHURN_ATIVOS[corte_txt])}"
          + (f" · saiu_60d {n(info['saiu'])} ({info['taxa']:.2f}%)" if "saiu" in info else ""))
    return base, info


def main() -> None:
    arquivos = [BRUTOS / x for x in ["assinaturas.csv", "eventos_assinatura.csv", "usuarios.csv", "pagamentos.csv", "uso_mensal.csv",
                                     "amizades.csv", "feed_posts.csv", "tickets_suporte.csv", "campanha_ago26.csv",
                                     "atividades.parquet"]]
    hash_antes = sha256(*arquivos)
    f = Fontes()
    print(f"[fontes] assinaturas {n(f.n_assin0)} → {n(f.n_assin)} sem cortesia/teste · pagamentos {n(f.pag_brutos)} (−{n(f.pag_dup)} duplicatas aprovadas) · "
          f"treinos (v2) {n(len(f.treinos))}")
    log: list[str] = []
    infos, bases = [], {}
    for corte, papel in CORTES:
        log.append(f"\n### Corte {corte[8:]}/{corte[5:7]}/{corte[:4]} ({papel})\n")
        log.append("| passo | linhas antes | linhas depois | observação |")
        log.append("|---|---|---|---|")
        b, info = construir(f, corte, papel, log)
        infos.append(info)
        bases[corte] = b

    # painel de treino + validação (com rótulo)
    rotulados = pd.concat([bases[c] for c, p in CORTES if p != "aplicação"], ignore_index=True)
    rotulados.to_parquet(PROC / "base_assinantes_painel_rotulado.parquet", index=False)
    print(f"[painel] {n(len(rotulados))} linhas rotuladas (3 cortes)")

    # verificações anti-vazamento e de consistência
    problemas = []
    for i in infos:
        corte = pd.Timestamp(i["corte"]) + pd.Timedelta(hours=23, minutes=59, seconds=59)
        for fonte, mx in i["max_datas"].items():
            ok = (pd.Period(mx, "M") <= corte.to_period("M")) if fonte == "uso_mensal" else (pd.Timestamp(mx) <= corte)
            if not ok:
                problemas.append(f"{i['corte']}: {fonte} usa {mx}")
        if i["ativos"] != i["ativos_serie"]:
            problemas.append(f"{i['corte']}: ativos {i['ativos']} ≠ série {i['ativos_serie']}")
        if "saiu" in i and i["saiu"] != i["saiu_direto"]:
            problemas.append(f"{i['corte']}: rótulo {i['saiu']} ≠ contagem direta {i['saiu_direto']}")
    print("[checagens] " + ("OK: ativos = série, rótulo = contagem direta, nenhuma fonte além do corte" if not problemas else "; ".join(problemas)))

    estado = "inalterados" if sha256(*arquivos) == hash_antes else "ALTERADOS"

    # relatório
    out = ["# Base de assinantes por corte (rótulo: sair em até 60 dias)\n",
           f"Gerado por `src/base_assinantes.py`. Só leitura dos brutos (SHA-256 conjunto `{hash_antes[:16]}…`, {estado}). "
           "Uma linha por assinante ativo no corte, sem contas de teste/cortesia; tudo medido até o corte (Brasília). Bases em `dados/processados/base_assinantes_<corte>.parquet` (fora do Git).\n",
           "## 1. Resumo por corte\n"]
    res = []
    for i in infos:
        res.append([i["corte"], i["papel"], n(i["ativos"]), n(i["ativos_serie"]), f"até {i['janela_fim']}",
                    n(i["saiu"]) if "saiu" in i else "—", f"{i['taxa']:.2f}%".replace(".", ",") if "taxa" in i else "—",
                    n(i["colunas"])])
    out.append(tabela(pd.DataFrame(res, columns=["corte", "papel", "ativos (base)", "ativos (série de churn)", "janela do rótulo",
                                                  "saiu em 60 dias", "taxa", "colunas"])) + "\n")
    out.append(f"Painel rotulado (30/04, 31/05 e 30/06): **{n(len(rotulados))}** linhas em `base_assinantes_painel_rotulado.parquet`.\n")
    out.append("## 2. Checagens\n")
    out.append("- Ativos de cada corte iguais à série de churn (`churn_mensal.csv`): " + ("✔" if not any("série" in p for p in problemas) else "✘") + ".")
    out.append("- Rótulo igual à contagem direta em `assinaturas.csv` (outro caminho de cálculo): " + ("✔" if not any("rótulo" in p for p in problemas) else "✘") + ".")
    out.append("- Data máxima usada por fonte e corte (nenhuma passa do corte): " + ("✔" if not any("usa" in p for p in problemas) else "✘") + ".\n")
    mx = []
    for i in infos:
        mx.append([i["corte"]] + [str(i["max_datas"].get(k, "—"))[:16] for k in ["eventos", "treinos", "pagamentos", "amizades", "posts", "tickets", "uso_mensal"]])
    out.append(tabela(pd.DataFrame(mx, columns=["corte", "eventos", "treinos", "pagamentos", "amizades", "posts", "tickets", "uso_mensal (mês)"])) + "\n")
    out.append("- Fim do período pago calculado (mensal: `inicio` + 30·k dias; anual: aniversário): bate com a `data_fim` real (no mensal, no primeiro ou no segundo fim de período) em " +
               "; ".join(f"{i['corte']}: {n(i['renov_bate'])} de {n(i['renov_n'])}" for i in infos if "renov_bate" in i) + " dos que saíram.")
    out.append("- Nulos que sobram nas colunas numéricas: " + "; ".join(f"{i['corte']}: idade {n(i['nulos_idade'])}, dias_semana_declarado {n(i['nulos_dias'])} (com marca), outras {n(i['nulos_outros'])}" for i in infos) + ".\n")
    out.append("## 3. Passos e junções (linhas antes e depois)\n")
    out += log
    out.append("\n## 4. Dicionário de variáveis\n")
    dic = [
        ["Identificação", "`user_id`, `assinatura_id`, `corte`, `inicio`, `tenure_dias`, `plano_atual`, `canal_cobranca`"],
        ["Rótulo (não é variável)", "`saiu_60d`, `rotulo_motivo_fim` (só nos cortes passados)"],
        ["Situação pelos eventos", "`renovacao_desligada`, `dias_desde_desligamento`, `n_renovacoes`, `n_carencia`, `tem_cancelamento_web`, `dias_ate_fim_periodo`"],
        ["Perfil", "`idade`, `flag_nascimento_invalido`, `sexo`, `uf`, `canal_aquisicao`, `sistema`, `relogio_conectado`, `flag_email_repetido`"],
        ["Onboarding", "`nivel_declarado`, `dias_semana_declarado`, `sem_questionario`, `nivel_nao_informado`, `dias_por_semana_nao_informado`, `objetivo_sem_resposta`"],
        ["Treinos", "`treinos_30d/60d/90d`, `minutos_30d/90d`, `km_90d`, `n_modalidades_90d`, `pct_relogio_90d`, `recencia_dias` (teto 90), `treinos_total`, `sem_treino_90d`, `tendencia`"],
        ["App", "`sessoes_app_mes`, `dias_ativos_mes`, `minutos_mes`, `sessoes_app_3m`, `minutos_3m`"],
        ["Pagamentos", "`pg_aprovados`, `pg_recusas`, `pg_recusas_90d`, `pg_estornos`, `pg_pct_recusa`, `pg_valor_medio`, `pg_metodo_principal`"],
        ["Social", "`n_seguindo`, `n_seguidores`, `n_posts`, `n_posts_90d`"],
        ["Suporte", "`n_tickets`, `n_tickets_90d`, `ticket_categoria_principal`"],
        ["Campanha (só 30/09)", "`grupo_campanha`, `camp_abriu_push`, `camp_abriu_email`, `camp_clicou`"],
    ]
    out.append(tabela(pd.DataFrame(dic, columns=["bloco", "variáveis"])) + "\n")
    out.append("Regras de vazio: contagens ausentes = 0; recência de quem não treinou = 90 (teto) com `sem_treino_90d`; tendência sem base = 1,0; categóricas vazias = `nao_informado`; idade NA quando o nascimento é inválido (com marca). Treinos já com as decisões 10, 11 (duplicata app removida), 23, 24 e 25 (`atividades_limpa_v2`); pagamentos sem duplicatas aprovadas (decisão 16).\n")
    out.append("## 5. Armadilhas\n")
    camp = [i for i in infos if i["papel"] == "validação"][0]
    out.append(f"- **Campanha de 10/08:** foi sorteada entre os pagantes ativos naquele dia. A janela do corte de 30/06 vai até {camp['janela_fim']} e passa de 10/08; quem saiu antes de 10/08 não podia ser sorteado, e o efeito da campanha entra no rótulo sem estar nas variáveis. Por isso o corte de 30/06 é só de validação e `grupo_campanha` existe apenas na base de 30/09.")
    out.append("- **Treinos só de 2026:** a janela de 90 dias só existe para cortes a partir de 31/03/2026 (por isso o primeiro corte é 30/04).")
    out.append("- **Plano e canal** vêm de `assinaturas.csv`; nos eventos nunca mudam por conta, então não há vazamento. A **renovação** vem só dos eventos até o corte (o retrato de 01/10 erra a situação de 36,6% das contas com renovação desligada).")
    out.append(f"- **Taxa de saída diferente por corte:** as janelas de 60 dias têm sazonalidade diferente; comparar taxas entre cortes exige cuidado.\n")
    out.append("## 6. Decisões propostas (formato do `decisoes.md`, não gravadas)\n")
    out.append("| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |")
    out.append("|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|")
    a30 = [i for i in infos if i["corte"] == "2026-09-30"][0]
    out.append(f"| 33 | 09/11/2026 | assinaturas.csv + eventos_assinatura.csv | base para prever a saída em 60 dias, sem vazamento | uma linha por assinante ativo no corte (sem cortesia/teste), com cortes de 30/04 e 31/05 (treino), 30/06 (validação) e 30/09 (aplicação); rótulo `saiu_60d` só nos cortes passados | o futuro de 30/09 ainda não aconteceu; janelas de treino antes da campanha de 10/08 | ativos: " + "; ".join(f"{i['corte']} {n(i['ativos'])}" for i in infos) + " |")
    out.append(f"| 34 | 09/11/2026 | eventos_assinatura.csv | o retrato de 01/10 erra a renovação nos cortes passados | situação da renovação pelo último evento de liga/desliga até o corte; plano e canal do retrato (não mudam nos eventos) | evita vazamento (análise 11: retrato erra 36,6%) | 0 linhas removidas |")
    out.append(f"| 35 | 09/11/2026 | atividades.parquet | treinos duplicados e outliers nas variáveis de engajamento | variáveis de treino a partir de `atividades_limpa_v2` (decisões 10, 11, 23 a 25); `recencia_dias` com teto 90 e marca `sem_treino_90d` | mesma limpeza das demais análises; janela de 90 dias é o que cabe em todos os cortes | linhas inalteradas |")
    out.append(f"| 36 | 09/11/2026 | campanha_ago26.csv | campanha só pode ser variável depois de 10/08 | `grupo_campanha` apenas na base de 30/09 ({n(a30.get('campanha_fora', 0))} ativos fora da campanha); corte de 30/06 só para validação | janela de 30/06 passa de 10/08 e o sorteio exclui quem já tinha saído | 0 linhas removidas |")
    out.append(f"\n---\nConferência: brutos {estado}.")
    RELATORIO.write_text("\n".join(out), encoding="utf-8")
    print(f"brutos {estado} · escrito: {RELATORIO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
