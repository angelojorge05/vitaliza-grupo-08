"""Base única para segmentação (K-means) e análise de churn — 1 linha por assinante.

Espinha (decisão A): os 14.059 pagantes ativos em 30/06/2026 com o rótulo saiu/ficou
do 3º trimestre e as features de engajamento — lidos de comportamento_ate_30jun.parquet
(gerado por src/comportamento_usuarios.py). Tudo medido até 30/06 (anti-vazamento).

Blocos adicionados (decisão C), todos com eventos filtrados até 30/06:
- perfil (usuarios.csv): idade em 30/06 (NA + flag quando nascimento inválido, decisão 5),
  sexo e sistema padronizados (mesmos mapas das decisões 2–3), uf, canal_aquisicao,
  relogio_conectado;
- onboarding.csv: nivel, dias_por_semana, como_conheceu — vazios e "-" viram
  "nao_informado" (decisões 7–8);
- pagamentos.csv (decisão B): duplicatas funcionais removidas dos aprovados pela chave
  validada (user_id + data/hora Brasília + valor + método + status + tentativa, mantém a
  primeira); features: nº de aprovados, nº de recusas, % recusa, valor médio pago,
  método principal;
- social: nº de seguidos/seguidores (amizades.csv, desde ≤ 30/06) e nº de posts;
- suporte: nº de tickets abertos até 30/06 e categoria principal.

Vazios numéricos (decisão D): contagens = 0; recência de quem não treinou = 181 dias
(teto do semestre) com a flag sem_treino_jan_jun; tendência sem base jan–abr = 1,0 (neutra).

Saídas: dados/processados/base_unica_30jun.parquet (fora do Git; regenerável) e
saidas/base_unica.md (dicionário de variáveis + contagens de construção).
"""

import pandas as pd

from utils import BRUTOS, PROCESSADOS, SAIDAS, mostrar, para_brasilia

REF = pd.Timestamp("2026-06-30 23:59:59")
MAPA_SEXO = {"F": "F", "Fem": "F", "feminino": "F", "M": "M", "Masc": "M", "masculino": "M"}
CHAVE_DEDUP_PAG = ["user_id", "dt_brt", "valor", "metodo", "status", "tentativa"]
NAO_INF = "nao_informado"


def fmt(n) -> str:
    return f"{n:,}".replace(",", ".")


def bloco_perfil(ids: set) -> pd.DataFrame:
    u = pd.read_csv(BRUTOS / "usuarios.csv", dtype=str,
                    usecols=["user_id", "data_nascimento", "sexo", "uf",
                             "canal_aquisicao", "sistema", "relogio_conectado"])
    u = u[u.user_id.isin(ids)]
    mostrar("perfil: usuarios da base", u)
    nasc = pd.to_datetime(u.pop("data_nascimento"), errors="coerce")
    invalido = (nasc > REF) | (nasc < "1920-01-01") | nasc.isna()
    u["idade"] = ((REF - nasc).dt.days / 365.25).round(1).where(~invalido)
    u["flag_nascimento_invalido"] = invalido
    u["sexo"] = u["sexo"].map(MAPA_SEXO).fillna(NAO_INF)
    u["sistema"] = u["sistema"].str.lower()
    u["relogio_conectado"] = u["relogio_conectado"].fillna("nenhum")
    print(f"  idades inválidas/ausentes: {fmt(int(invalido.sum()))}")
    return u


def bloco_onboarding(ids: set) -> pd.DataFrame:
    o = pd.read_csv(BRUTOS / "onboarding.csv", dtype=str,
                    usecols=["user_id", "nivel", "dias_por_semana", "como_conheceu"])
    o = o[o.user_id.isin(ids)]
    mostrar("onboarding: respostas da base", o)
    for c in ["nivel", "dias_por_semana", "como_conheceu"]:
        v = o[c].astype("string").str.strip()
        o[c] = v.where(v.notna() & (v != "") & (v != "-"), NAO_INF)
    # grafias mistas ("3", "3x", "3 vezes") -> extrai o dígito; vazio segue NA
    extraido = o["dias_por_semana"].astype("string").str.extract(r"(\d)")[0]
    n_texto = int((o["dias_por_semana"].astype("string").str.strip().str.len() > 1).sum())
    o["dias_por_semana"] = pd.to_numeric(extraido, errors="coerce")
    print(f"  dias_por_semana em texto normalizados: {fmt(n_texto)} "
          f"| sem resposta: {fmt(int(o['dias_por_semana'].isna().sum()))}")
    return o.rename(columns={"nivel": "nivel_declarado", "dias_por_semana": "dias_semana_declarado"})


def bloco_pagamentos(ids: set) -> pd.DataFrame:
    p = pd.read_csv(BRUTOS / "pagamentos.csv",
                    dtype={"user_id": str, "metodo": str, "status": str, "valor": str})
    mostrar("pagamentos lidos", p)
    # valor em 2 formatos: "99.99" e "R$ 99,99" -> número
    p["valor"] = pd.to_numeric(
        p["valor"].str.replace("R$", "", regex=False).str.strip()
                  .str.replace(",", ".", regex=False), errors="coerce")
    print(f"  valores não interpretados: {int(p['valor'].isna().sum())}")
    p["dt_brt"] = para_brasilia(p["data_hora"])
    p = p[(p.dt_brt <= REF) & p.user_id.isin(ids)]
    mostrar("até 30/06 e da base", p)

    ap = p[p.status == "aprovado"].copy()
    dup = ap.duplicated(subset=CHAVE_DEDUP_PAG, keep="first")
    print(f"  duplicatas funcionais removidas (aprovados): {fmt(int(dup.sum()))} "
          f"| R$ {ap.loc[dup, 'valor'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    ap = ap[~dup]
    rec = p[p.status == "recusado"]

    f = pd.DataFrame({
        "pg_aprovados": ap.groupby("user_id").size(),
        "pg_valor_medio": ap.groupby("user_id")["valor"].mean().round(2),
        "pg_metodo_principal": ap.groupby("user_id")["metodo"].agg(lambda s: s.mode().iat[0]),
        "pg_recusas": rec.groupby("user_id").size(),
    })
    f["pg_recusas"] = f["pg_recusas"].fillna(0).astype(int)
    f["pg_pct_recusa"] = (100 * f.pg_recusas / (f.pg_recusas + f.pg_aprovados.fillna(0))).round(1)
    print(f"  usuários com cobrança no período: {fmt(len(f))}")
    return f.reset_index()


def bloco_social(ids: set) -> pd.DataFrame:
    a = pd.read_csv(BRUTOS / "amizades.csv", dtype=str)
    a["desde"] = pd.to_datetime(a["desde"], errors="coerce")
    a = a[a.desde <= REF]
    mostrar("amizades até 30/06", a)
    seguindo = a[a.seguidor_id.isin(ids)].groupby("seguidor_id").size()
    seguidores = a[a.seguido_id.isin(ids)].groupby("seguido_id").size()

    fp = pd.read_csv(BRUTOS / "feed_posts.csv", dtype={"user_id": str}, usecols=["user_id", "data_hora"])
    fp["dt"] = para_brasilia(fp["data_hora"])
    fp = fp[(fp.dt <= REF) & fp.user_id.isin(ids)]
    mostrar("posts até 30/06 e da base", fp)

    f = pd.DataFrame({"n_seguindo": seguindo, "n_seguidores": seguidores,
                      "n_posts": fp.groupby("user_id").size()})
    return f.fillna(0).astype(int).reset_index().rename(columns={"index": "user_id"})


def bloco_suporte(ids: set) -> pd.DataFrame:
    t = pd.read_csv(BRUTOS / "tickets_suporte.csv", dtype=str,
                    usecols=["user_id", "aberto_em", "categoria_atendente"])
    t["aberto_em"] = para_brasilia(t["aberto_em"])
    t = t[(t.aberto_em <= REF) & t.user_id.isin(ids)]
    mostrar("tickets até 30/06 e da base", t)
    f = pd.DataFrame({
        "n_tickets": t.groupby("user_id").size(),
        "ticket_categoria_principal": t.groupby("user_id")["categoria_atendente"]
            .agg(lambda s: s.mode().iat[0] if s.notna().any() else NAO_INF),
    })
    return f.reset_index()


def main() -> None:
    espinha = pd.read_parquet(PROCESSADOS / "comportamento_ate_30jun.parquet")
    mostrar("espinha: comportamento_ate_30jun", espinha)
    ids = set(espinha.user_id)

    blocos = [bloco_perfil(ids), bloco_onboarding(ids), bloco_pagamentos(ids),
              bloco_social(ids), bloco_suporte(ids)]
    base = espinha
    for b in blocos:
        antes = len(base)
        base = base.merge(b, on="user_id", how="left")
        assert len(base) == antes, f"junção multiplicou linhas ({antes} -> {len(base)})"
    mostrar("base única após 5 junções 1:1", base)

    # decisão D: vazios
    base["recencia_dias"] = base["recencia_dias"].fillna(181).clip(upper=181).astype(int)
    base["tendencia"] = base["tendencia"].fillna(1.0)
    for c in ["pg_aprovados", "pg_recusas", "n_seguindo", "n_seguidores", "n_posts",
              "n_tickets", "n_modalidades"]:
        base[c] = base[c].fillna(0).astype(int)
    for c in ["pct_relogio", "sessoes_app_mes", "dias_ativos_mes", "minutos_mes"]:
        base[c] = base[c].fillna(0.0)
    base["pg_pct_recusa"] = base["pg_pct_recusa"].fillna(0.0)
    for c in ["nivel_declarado", "como_conheceu", "pg_metodo_principal", "ticket_categoria_principal"]:
        base[c] = base[c].fillna(NAO_INF)

    PROCESSADOS.mkdir(parents=True, exist_ok=True)
    destino = PROCESSADOS / "base_unica_30jun.parquet"
    base.to_parquet(destino, index=False)
    nums = base.select_dtypes("number").columns
    print(f"\n[saída] {destino.name}: {fmt(len(base))} linhas × {base.shape[1]} colunas "
          f"({len(nums)} numéricas) · NAs restantes nas numéricas: {int(base[nums].isna().sum().sum())} (só idade)")

    # dicionário de variáveis
    grupos_dic = {
        "Identificação e rótulo": ["user_id", "grupo", "plano_atual", "canal_cobranca", "inicio", "data_fim"],
        "Engajamento (treinos tratados)": ["treinos_jan_jun", "minutos_jan_jun", "treinos_30d", "treinos_60d",
                                           "treinos_90d", "recencia_dias", "n_modalidades", "pct_relogio",
                                           "tendencia", "sem_treino_jan_jun"],
        "App (uso_mensal 2026)": ["sessoes_app_mes", "dias_ativos_mes", "minutos_mes"],
        "Perfil (usuarios)": ["idade", "flag_nascimento_invalido", "sexo", "uf", "canal_aquisicao",
                              "sistema", "relogio_conectado"],
        "Onboarding": ["nivel_declarado", "dias_semana_declarado", "como_conheceu"],
        "Pagamentos (dedup, até 30/06)": ["pg_aprovados", "pg_recusas", "pg_pct_recusa",
                                          "pg_valor_medio", "pg_metodo_principal"],
        "Social": ["n_seguindo", "n_seguidores", "n_posts"],
        "Suporte": ["n_tickets", "ticket_categoria_principal"],
    }
    linhas = [
        "# Base única · pagantes em 30/06 com rótulo saiu/ficou",
        "",
        f"Gerada por `src/base_unica.py`: **{fmt(len(base))} assinantes × {base.shape[1]} variáveis**, "
        "tudo medido até 30/06/2026 (anti-vazamento); rótulo = fim de assinatura em jul–set. "
        "Insumo para o K-means de personas e para a modelagem de churn. O arquivo fica em "
        "`dados/processados/` (fora do Git): regenerar com `python src/comportamento_usuarios.py` "
        "e depois `python src/base_unica.py`.",
        "",
        "| Bloco | Variáveis |",
        "|---|---|",
    ]
    for g, cols in grupos_dic.items():
        linhas.append(f"| {g} | {', '.join('`'+c+'`' for c in cols)} |")
    linhas += [
        "",
        "Regras aplicadas: duplicatas funcionais de pagamentos removidas (chave "
        "user_id + data/hora Brasília + valor + método + status + tentativa, só aprovados); "
        "vazios de contagem = 0; recência sem treino = 181 + flag; tendência sem base = 1,0; "
        "categóricas vazias = `nao_informado`; idade NA quando nascimento inválido (com flag).",
    ]
    (SAIDAS / "base_unica.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"[saída] {SAIDAS / 'base_unica.md'}")


if __name__ == "__main__":
    main()
