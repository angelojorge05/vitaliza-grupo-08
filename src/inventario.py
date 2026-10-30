"""Inventário de dados/brutos/: linhas, colunas, tipos e vazios de cada arquivo,
comparados com o dicionário de dados (docs/).

Só lê os arquivos brutos (um por vez) e grava apenas saidas/inventario.md.
Nenhuma limpeza é feita: fusos e contas de teste são só contados.
"""

import gc
import hashlib
import re
import struct
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos"
SAIDA = RAIZ / "saidas" / "inventario.md"

CORTE = pd.Timestamp("2026-09-30 23:59:59")
FUSO = "America/Sao_Paulo"
MARCADORES = {"null", "none", "na", "n/a", "nan", "-", "--", "?"}

CANAL_COBRANCA = ["app_store", "google_play", "web_cartao", "web_pix"]
PLANO = ["mensal", "anual"]

# Tudo o que o dicionário (docs/Vitaliza - Dicionário de dados.pdf) afirma e dá para conferir.
# faixas: (início, fim) esperado de cada coluna de data; fim None = só a checagem do corte.
# refs: colunas que devem existir em usuarios.csv ("o user_id liga todos os arquivos").
DICIONARIO = {
    "usuarios.csv": dict(
        por="conta", linhas=64_948,
        colunas=["user_id", "email", "data_cadastro", "data_nascimento", "sexo", "cidade", "uf",
                 "cep_prefixo", "canal_aquisicao", "sistema", "versao_app", "relogio_conectado"],
        chaves=[["user_id"]], faixas={"data_cadastro": ("2020-09-01", None)}),
    "assinaturas.csv": dict(
        por="assinatura (retrato de 01/10/2026)", linhas=32_643,
        colunas=["assinatura_id", "user_id", "plano_atual", "canal_cobranca", "inicio",
                 "status_atual", "renovacao_automatica", "data_fim", "motivo_fim"],
        chaves=[["assinatura_id"]], refs=["user_id"],
        categorias={"plano_atual": PLANO, "canal_cobranca": CANAL_COBRANCA},
        faixas={"inicio": ("2020-09-01", None)}),
    "amizades.csv": dict(
        por="relação de seguir", linhas=113_480,
        colunas=["seguidor_id", "seguido_id", "desde"],
        chaves=[["seguidor_id", "seguido_id"]], refs=["seguidor_id", "seguido_id"]),
    "campanha_ago26.csv": dict(
        por="assinante sorteado", linhas=14_120,
        colunas=["user_id", "grupo", "enviado_em", "canal", "titulo_mensagem", "oferta",
                 "abriu_push", "abriu_email", "clicou"],
        chaves=[["user_id"]], refs=["user_id"],
        categorias={"grupo": ["controle", "desafio", "cupom", "conteudo"],
                    "canal": ["push+email"], "oferta": ["30pct_3_meses", "1_mes_gratis"]},
        faixas={"enviado_em": ("2026-08-10", "2026-08-10 23:59:59")}),
    "eventos_assinatura.csv": dict(
        por="evento", linhas=275_565,
        colunas=["user_id", "data_hora", "evento", "plano", "canal_cobranca", "detalhe"],
        refs=["user_id"],
        categorias={"evento": ["trial_iniciado", "trial_expirado", "assinatura_iniciada",
                               "renovacao", "renovacao_automatica_desligada",
                               "renovacao_automatica_religada", "periodo_carencia",
                               "assinatura_expirada", "cancelamento_web", "reembolso",
                               "chargeback"],
                    "plano": PLANO, "canal_cobranca": CANAL_COBRANCA},
        faixas={"data_hora": ("2024-07-01", None)}),
    "pagamentos.csv": dict(
        por="tentativa de cobrança", linhas=165_548,
        colunas=["pagamento_id", "user_id", "data_hora", "valor", "metodo", "status", "tentativa"],
        chaves=[["pagamento_id"]], refs=["user_id"],
        categorias={"metodo": ["app_store", "google_play", "cartao", "pix_automatico"],
                    "status": ["aprovado", "recusado", "estornado", "chargeback"]}),
    "uso_mensal.csv": dict(
        por="usuário e mês", linhas=591_662,
        colunas=["user_id", "mes", "atividades", "atividades_ar_livre", "atividades_video",
                 "minutos", "dias_ativos", "sessoes_app"],
        chaves=[["user_id", "mes"]], refs=["user_id"],
        faixas={"mes": ("2025-01-01", None)}),
    "atividades.parquet": dict(
        por="treino", linhas=1_254_475,
        colunas=["atividade_id", "user_id", "inicio", "tipo", "duracao_min", "distancia_km",
                 "ritmo_min_km", "fc_media", "origem", "gps_ok", "treino_com"],
        chaves=[["atividade_id"]], refs=["user_id", "treino_com"],
        categorias={"origem": ["app", "garmin", "apple_health"]},
        faixas={"inicio": ("2026-01-01", None)}),
    "onboarding.csv": dict(
        por="conta", linhas=63_929,
        colunas=["onboarding_id", "user_id", "respondido_em", "objetivo_texto", "como_conheceu",
                 "nivel", "dias_por_semana"],
        chaves=[["onboarding_id"], ["user_id"]], refs=["user_id"],
        faixas={"respondido_em": ("2020-09-01", None)}),
    "pesquisa_saida.csv": dict(
        por="resposta", linhas=643, contas=641,
        colunas=["resposta_id", "user_id", "respondido_em", "motivo_principal", "comentario"],
        chaves=[["resposta_id"]], refs=["user_id"],
        categorias={"motivo_principal": ["preco", "nao_uso", "problema_tecnico", "outro_app",
                                         "saude", "outro"]},
        faixas={"respondido_em": ("2026-06-01", None)}),
    "feed_posts.csv": dict(
        por="post", linhas=119_309,
        colunas=["post_id", "user_id", "data_hora", "texto", "curtidas"],
        chaves=[["post_id"]], refs=["user_id"],
        faixas={"data_hora": ("2025-07-01", None)}),
    "tickets_suporte.csv": dict(
        por="chamado", linhas=4_422,
        colunas=["ticket_id", "user_id", "aberto_em", "canal", "texto_cliente",
                 "categoria_atendente", "status", "resolvido_em"],
        chaves=[["ticket_id"]], refs=["user_id"],
        categorias={"canal": ["chat", "email", "loja"],
                    "status": ["resolvido", "aberto", "sem_resposta"]},
        faixas={"aberto_em": ("2025-07-01", None)}),
}

HEATMAPS_ESPERADO = {"2026-07-31": 12_426, "2026-09-30": 13_047}

# Classificação do conteúdo de colunas de texto; a ordem importa (o primeiro padrão vence).
HORA = r"[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?"
PADROES = [
    ("data e hora UTC (Z)", rf"\d{{4}}-\d{{2}}-\d{{2}}{HORA}Z"),
    ("data e hora com fuso", rf"\d{{4}}-\d{{2}}-\d{{2}}{HORA}[+-]\d{{2}}:?\d{{2}}"),
    ("data e hora", rf"\d{{4}}-\d{{2}}-\d{{2}}{HORA}"),
    ("data", r"\d{4}-\d{2}-\d{2}"),
    ("data e hora DD/MM/AAAA", r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}(:\d{2})?"),
    ("data DD/MM/AAAA", r"\d{2}/\d{2}/\d{4}"),
    ("mês AAAA-MM", r"\d{4}-\d{2}"),
    ("booleano", r"(?i:true|false)"),
    ("inteiro", r"-?[1-9]\d*|0"),
    ("número com zero à esquerda", r"0\d+"),
    ("decimal", r"-?\d+\.\d+"),
    ("decimal com vírgula", r"-?\d+,\d+"),
]
ROTULOS_NUMERO = {"inteiro", "decimal", "decimal com vírgula"}
TIPOS_PNG = {0: "escala de cinza", 2: "RGB", 3: "paleta", 4: "cinza + alfa", 6: "RGBA"}


# ---------- formatação ----------

def fmt(n) -> str:
    return f"{n:,}".replace(",", ".")


def pct(a, b) -> str:
    return f"{100 * a / b:.1f}%".replace(".", ",") if b else "-"


def md(valor, n=40) -> str:
    s = str(valor).replace("|", "\\|").replace("\n", " ").replace("\r", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def fmt_valor(v) -> str:
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return "-"
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d") if v == v.normalize() else v.strftime("%Y-%m-%d %H:%M")
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def mascarar_email(v: str) -> str:
    return re.sub(r"^[^@]*", "***", v)


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


# ---------- leitura ----------

def ler_csv(caminho: Path):
    with open(caminho, "rb") as f:
        cabecalho = f.readline()
    bom = cabecalho.startswith(b"\xef\xbb\xbf")
    try:
        cabecalho.decode("utf-8-sig")
        encoding = "utf-8-sig"
    except UnicodeDecodeError:
        encoding = "latin-1"
    linha = cabecalho.decode(encoding)
    sep = max([",", ";", "\t", "|"], key=linha.count)
    # dtype=str + keep_default_na=False: o arquivo como veio, sem conversão nem NaN automático
    df = pd.read_csv(caminho, dtype=str, keep_default_na=False, sep=sep, encoding=encoding)
    palpite = pd.read_csv(caminho, sep=sep, encoding=encoding, low_memory=False).dtypes
    info = dict(sep={"\t": "tab"}.get(sep, sep), encoding="utf-8" if encoding == "utf-8-sig" else encoding,
                bom=bom)
    return df, {c: str(t) for c, t in palpite.items()}, info


# ---------- perfil de coluna ----------

def classificar(valores: pd.Series, contagens: pd.Series) -> tuple[Counter, dict]:
    """Conta valores por tipo e guarda os 3 exemplos mais frequentes de cada tipo."""
    resto = pd.Series(True, index=valores.index)
    tipos, exemplos = Counter(), {}
    for rotulo, padrao in PADROES + [("texto", r"(?s:.*)")]:
        m = resto & valores.str.fullmatch(padrao)
        if m.any():
            tipos[rotulo] += int(contagens[m].sum())
            exemplos[rotulo] = list(valores[m].head(3))
        resto &= ~m
    return tipos, exemplos


def normalizar(s: pd.Series) -> pd.Series:
    """Minúsculas, sem acento e sem espaços nas pontas, para achar variações de escrita."""
    return (s.str.strip().str.lower().str.normalize("NFKD")
            .str.encode("ascii", errors="ignore").str.decode("ascii"))


def para_datetime(s: pd.Series) -> pd.Series:
    """Converte textos de data para horário de Brasília (sem fuso). O que não casa vira NaT."""
    partes = []
    ingenuo = s.str.fullmatch(rf"\d{{4}}-\d{{2}}-\d{{2}}({HORA})?")
    if ingenuo.any():
        partes.append(pd.to_datetime(s[ingenuo], format="ISO8601", errors="coerce"))
    com_fuso = s.str.fullmatch(rf"\d{{4}}-\d{{2}}-\d{{2}}{HORA}(Z|[+-]\d{{2}}:?\d{{2}})")
    if com_fuso.any():
        utc = pd.to_datetime(s[com_fuso], format="ISO8601", utc=True, errors="coerce")
        partes.append(utc.dt.tz_convert(FUSO).dt.tz_localize(None))
    br = s.str.fullmatch(r"\d{2}/\d{2}/\d{4}( \d{2}:\d{2}(:\d{2})?)?")
    if br.any():
        partes.append(pd.to_datetime(s[br], dayfirst=True, format="mixed", errors="coerce"))
    mes = s.str.fullmatch(r"\d{4}-\d{2}")
    if mes.any():
        partes.append(pd.to_datetime(s[mes], format="%Y-%m", errors="coerce"))
    if not partes:
        return pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    partes = [p.astype("datetime64[ns]") for p in partes]
    return pd.concat(partes).reindex(s.index)


def perfil_texto(serie: pd.Series, faixa) -> dict:
    nulos = int(serie.isna().sum())
    s = serie.dropna().astype(str)
    limpo = s.str.strip()
    m_vazio = limpo == ""
    m_marc = limpo.str.lower().isin(MARCADORES)
    validos = limpo[~m_vazio & ~m_marc]
    vc = validos.value_counts()
    valores = pd.Series(vc.index.astype(str))
    contagens = pd.Series(vc.to_numpy())
    tipos, exemplos = classificar(valores, contagens)
    p = dict(nulos=nulos, vazios=int(m_vazio.sum()), marcadores=int(m_marc.sum()),
             marcadores_vistos=Counter(limpo[m_marc]).most_common(3),
             espacos=int(((s != limpo) & ~m_vazio).sum()), distintos=len(vc),
             tipos=tipos, exemplos=exemplos, n_validos=len(validos), top=list(vc.head(12).items()))
    n = len(validos)
    n_datas = sum(c for r, c in tipos.items() if r.startswith(("data", "mês")))
    n_numeros = sum(c for r, c in tipos.items() if r in ROTULOS_NUMERO)
    if n and n_datas / n > 0.5:
        dt = para_datetime(validos)
        formas = valores.str.replace(r"\d", "9", regex=True)
        formatos = contagens.groupby(formas.to_numpy()).sum().sort_values(ascending=False)
        p.update(eh_data=True, minimo=dt.min(), maximo=dt.max(),
                 nao_interpretaveis=int(dt.isna().sum()),
                 utc_z=int(validos.str.endswith("Z").sum()),
                 depois_corte=int((dt > CORTE).sum()),
                 formatos=list(formatos.head(6).items()))
        if faixa:
            ini, fim = faixa
            p["antes_inicio"] = int((dt < pd.Timestamp(ini)).sum()) if ini else 0
            p["depois_fim"] = int((dt > pd.Timestamp(fim)).sum()) if fim else 0
    elif n and n_numeros / n > 0.5:
        x = pd.to_numeric(validos.str.replace(",", ".", regex=False), errors="coerce")
        p.update(minimo=x.min(), maximo=x.max())
    return p


def perfil_nativo(serie: pd.Series) -> dict:
    validos = serie.dropna()
    if pd.api.types.is_bool_dtype(serie):
        rotulo = "booleano"
    elif pd.api.types.is_integer_dtype(serie):
        rotulo = "inteiro"
    elif pd.api.types.is_datetime64_any_dtype(serie):
        rotulo = "data e hora"
    else:
        rotulo = "decimal"
    p = dict(nulos=int(serie.isna().sum()), vazios=0, marcadores=0, marcadores_vistos=[],
             espacos=0, distintos=int(validos.nunique()), tipos=Counter({rotulo: len(validos)}),
             exemplos={}, n_validos=len(validos), top=list(validos.value_counts().head(12).items()))
    if rotulo != "booleano" and len(validos):
        p.update(minimo=validos.min(), maximo=validos.max())
    return p


def perfil_coluna(serie: pd.Series, faixa) -> dict:
    nativo = (pd.api.types.is_bool_dtype(serie) or pd.api.types.is_numeric_dtype(serie)
              or pd.api.types.is_datetime64_any_dtype(serie))
    return perfil_nativo(serie) if nativo else perfil_texto(serie, faixa)


def descrever_tipos(tipos: Counter, n: int) -> str:
    if not n:
        return "(sem valores)"
    return " · ".join(f"{r} {pct(c, n)}" for r, c in tipos.most_common())


# ---------- checagens contra o dicionário ----------

def valores_validos(serie: pd.Series) -> pd.Series:
    v = serie.dropna().astype(str).str.strip()
    return v[(v != "") & ~v.str.lower().isin(MARCADORES)]


def checar_categorias(serie: pd.Series, permitidos: list[str]):
    vc = valores_validos(serie).value_counts()
    baixos = {p.lower() for p in permitidos}
    fora = [(v, int(n), v.lower() in baixos) for v, n in vc.items() if v not in permitidos]
    return fora


def analisar_arquivo(nome: str, spec: dict, ids_usuarios: set | None):
    caminho = BRUTOS / nome
    if caminho.suffix == ".parquet":
        df = pd.read_parquet(caminho)
        palpite = {c: str(t) for c, t in df.dtypes.items()}
        info = dict(formato="parquet")
    else:
        df, palpite, info = ler_csv(caminho)
        info["formato"] = "csv"

    total = len(df)
    faixas = spec.get("faixas", {})
    perfis = {c: perfil_coluna(df[c], faixas.get(c)) for c in df.columns}

    div, obs = [], []

    # linhas
    if total != spec["linhas"]:
        div.append(f"Linhas: {fmt(total)} encontradas, {fmt(spec['linhas'])} no dicionário "
                   f"(diferença de {fmt(total - spec['linhas'])}).")

    # colunas
    esperadas, achadas = spec["colunas"], list(df.columns)
    faltam = [c for c in esperadas if c not in achadas]
    sobram = [c for c in achadas if c not in esperadas]
    if faltam:
        div.append("Colunas do dicionário ausentes no arquivo: " + ", ".join(f"`{c}`" for c in faltam) + ".")
    if sobram:
        div.append("Colunas no arquivo que o dicionário não descreve: " + ", ".join(f"`{c}`" for c in sobram) + ".")
    if not faltam and not sobram and achadas != esperadas:
        obs.append("As colunas estão numa ordem diferente da do dicionário.")

    # duplicatas
    dup_total = int(df.duplicated().sum())
    if dup_total:
        div.append(f"{fmt(dup_total)} linhas são cópias exatas de outra linha.")
    for chave in spec.get("chaves", []):
        if not all(c in df.columns for c in chave):
            continue
        k = df[chave].astype(str).apply(lambda col: col.str.strip())
        m = k.duplicated(keep=False)
        if m.any():
            nome_chave = " + ".join(f"`{c}`" for c in chave)
            div.append(f"Dicionário diz \"uma linha por {spec['por']}\", mas {nome_chave} se repete: "
                       f"{fmt(int(m.sum()))} linhas em {fmt(int(k[m].drop_duplicates().shape[0]))} "
                       f"valores repetidos.")

    if "contas" in spec and "user_id" in df.columns:
        n_contas = valores_validos(df["user_id"]).nunique()
        if n_contas != spec["contas"]:
            div.append(f"Contas distintas: {fmt(n_contas)}, {fmt(spec['contas'])} no dicionário.")

    # categorias
    for col, permitidos in spec.get("categorias", {}).items():
        if col not in df.columns:
            continue
        fora = checar_categorias(df[col], permitidos)
        if fora:
            n_linhas = sum(n for _, n, _ in fora)
            itens = ", ".join(f"`{md(v, 30)}` ({fmt(n)}{', só muda a escrita' if variacao else ''})"
                              for v, n, variacao in fora[:10])
            mais = f" e mais {len(fora) - 10}" if len(fora) > 10 else ""
            div.append(f"`{col}`: {len(fora)} valores fora da lista do dicionário, em {fmt(n_linhas)} "
                       f"linhas: {itens}{mais}.")

    # datas: faixas do dicionário e corte
    for col, p in perfis.items():
        if not p.get("eh_data"):
            continue
        if p.get("antes_inicio"):
            div.append(f"`{col}`: {fmt(p['antes_inicio'])} linhas antes de {faixas[col][0]}, "
                       f"início do período que o dicionário descreve.")
        if p.get("depois_fim"):
            div.append(f"`{col}`: {fmt(p['depois_fim'])} linhas depois de {faixas[col][1]}, "
                       f"fim do período que o dicionário descreve.")
        if p["depois_corte"]:
            div.append(f"`{col}`: {fmt(p['depois_corte'])} linhas depois da data de corte "
                       f"(30/09/2026, já em horário de Brasília).")
        if p["nao_interpretaveis"]:
            obs.append(f"`{col}`: {fmt(p['nao_interpretaveis'])} valores que não são datas reconhecíveis.")
        if len(p["formatos"]) > 1:
            formatos = ", ".join(f"`{f}` ({fmt(int(n))})" for f, n in p["formatos"])
            obs.append(f"`{col}`: {len(p['formatos'])} formatos de data diferentes: {formatos}.")
        if p["utc_z"]:
            obs.append(f"`{col}`: {fmt(p['utc_z'])} valores em UTC (terminam em `Z`); "
                       f"os demais não indicam fuso.")

    # integridade com usuarios.csv
    if ids_usuarios is not None:
        for col in spec.get("refs", []):
            if col not in df.columns:
                continue
            v = valores_validos(df[col])
            fora = ~v.isin(ids_usuarios)
            if fora.any():
                div.append(f"`{col}`: {fmt(int(fora.sum()))} linhas ({fmt(int(v[fora].nunique()))} contas) "
                           f"com id que não existe em `usuarios.csv`.")

    # observações de qualidade
    for col, p in perfis.items():
        if p["espacos"]:
            obs.append(f"`{col}`: {fmt(p['espacos'])} valores com espaços no começo ou no fim.")
        if p["marcadores"]:
            vistos = ", ".join(f"`{m}` ({fmt(n)})" for m, n in p["marcadores_vistos"])
            obs.append(f"`{col}`: {fmt(p['marcadores'])} valores que parecem marcar ausência: {vistos}.")
        if p["tipos"].get("decimal com vírgula"):
            obs.append(f"`{col}`: {fmt(p['tipos']['decimal com vírgula'])} decimais com vírgula.")
        if p["tipos"].get("número com zero à esquerda"):
            obs.append(f"`{col}`: {fmt(p['tipos']['número com zero à esquerda'])} números com zero à "
                       f"esquerda (manter como texto).")
        rotulos = [r for r in p["tipos"] if r != "texto"]
        if p["tipos"].get("texto") and rotulos and p["tipos"]["texto"] < 0.5 * p["n_validos"]:
            ex = ", ".join(f"`{md(v, 25)}`" for v in p["exemplos"]["texto"])
            obs.append(f"`{col}`: mistura tipos ({descrever_tipos(p['tipos'], p['n_validos'])}); "
                       f"exemplos do que não é número: {ex}.")
        if 1 < p["distintos"] <= 60 and not p.get("eh_data") and col not in spec.get("categorias", {}):
            vals = valores_validos(df[col])
            chave = normalizar(vals)
            grupos = vals.groupby(chave).nunique()
            variantes = grupos[grupos > 1]
            if len(variantes):
                exemplos = []
                for base in variantes.index[:6]:
                    formas = sorted(vals[chave == base].unique())
                    exemplos.append(" / ".join(f"`{md(f, 20)}`" for f in formas))
                obs.append(f"`{col}`: o mesmo valor aparece escrito de jeitos diferentes "
                           f"(maiúsculas ou acentos): " + "; ".join(exemplos) + ".")

    if info.get("bom"):
        obs.append("O arquivo começa com BOM (marca de byte UTF-8).")
    if info.get("encoding") not in (None, "utf-8"):
        obs.append(f"Codificação do arquivo: {info['encoding']}, não UTF-8.")
    if info.get("sep") not in (None, ","):
        obs.append(f"Separador de colunas: `{info['sep']}`, não vírgula.")

    extra = {}
    if nome == "usuarios.csv":
        emails = valores_validos(df["email"]).str.lower()
        extra["contas_teste"] = int(emails.str.endswith("@vitaliza.com.br").sum())
        obs.append(f"Contas de teste (`@vitaliza.com.br`, sem diferenciar maiúsculas): "
                   f"{fmt(extra['contas_teste'])}. Só contadas aqui; a regra do CLAUDE.md é excluí-las.")

    ids = set(valores_validos(df["user_id"])) if nome == "usuarios.csv" else None

    resultado = dict(nome=nome, spec=spec, total=total, colunas=achadas, palpite=palpite,
                     perfis=perfis, div=div, obs=obs, info=info, dup_total=dup_total, extra=extra)
    del df
    gc.collect()
    return resultado, ids


def eh_metadado_mac(nome: str) -> bool:
    return nome.startswith("__MACOSX/") or Path(nome).name.startswith("._")


def analisar_heatmaps(caminho: Path, ids_usuarios: set) -> dict:
    data = re.search(r"\d{4}-\d{2}-\d{2}", caminho.name).group()
    with zipfile.ZipFile(caminho) as z:
        todos = [i for i in z.infolist() if not i.is_dir()]
        metadados = [i for i in todos if eh_metadado_mac(i.filename)]
        arquivos = [i for i in todos if not eh_metadado_mac(i.filename)]
        extensoes = Counter(Path(i.filename).suffix.lower() or "(sem extensão)" for i in arquivos)
        pastas = Counter(str(Path(i.filename).parent).replace("\\", "/") for i in arquivos)
        pngs = [i for i in arquivos if i.filename.lower().endswith(".png")]
        passo = max(1, len(pngs) // 50)
        amostra = pngs[::passo][:50]
        cabecalhos, assinatura_ok = Counter(), 0
        for i in amostra:
            with z.open(i) as f:
                h = f.read(33)
            if h[:8] == b"\x89PNG\r\n\x1a\n" and h[12:16] == b"IHDR":
                assinatura_ok += 1
                largura, altura = struct.unpack(">II", h[16:24])
                cabecalhos[(largura, altura, h[24], h[25])] += 1
        nomes = [Path(i.filename).stem for i in pngs]
        tamanhos = [i.file_size for i in pngs]
    repetidos = sum(n - 1 for n in Counter(nomes).values() if n > 1)
    fora = [n for n in nomes if n not in ids_usuarios]

    div, obs = [], []
    if metadados:
        obs.append(f"`{caminho.name}`: {fmt(len(metadados))} arquivos de metadados do macOS "
                   f"(`__MACOSX/`, nomes `._…`, {sum(i.file_size for i in metadados)} bytes no total). "
                   f"Não são imagens; ficaram fora das contagens.")
    esperado = HEATMAPS_ESPERADO.get(data)
    if esperado is not None and len(pngs) != esperado:
        div.append(f"{fmt(len(pngs))} imagens, {fmt(esperado)} no dicionário "
                   f"(diferença de {fmt(len(pngs) - esperado)}).")
    nao_png = len(arquivos) - len(pngs)
    if nao_png:
        div.append(f"{fmt(nao_png)} arquivos que não são PNG.")
    if not any(p.rstrip("/").endswith(data) for p in pastas):
        div.append(f"Nenhuma pasta `{data}/`, como o dicionário descreve.")
    if fora:
        div.append(f"{fmt(len(fora))} imagens com nome que não é um `user_id` de `usuarios.csv` "
                   f"(ex.: {', '.join(f'`{md(n, 30)}`' for n in fora[:3])}).")
    if repetidos:
        div.append(f"{fmt(repetidos)} nomes de imagem repetidos.")
    if assinatura_ok < len(amostra):
        div.append(f"{len(amostra) - assinatura_ok} das {len(amostra)} imagens da amostra não têm "
                   f"cabeçalho PNG válido.")

    return dict(nome=f"heatmaps/{caminho.name}", data=data, arquivos=len(arquivos), pngs=len(pngs),
                extensoes=extensoes, pastas=pastas, amostra=len(amostra), assinatura_ok=assinatura_ok,
                cabecalhos=cabecalhos, tamanhos=tamanhos, esperado=esperado, div=div, obs=obs,
                metadados=len(metadados), tamanho_zip=caminho.stat().st_size)


# ---------- relatório ----------

def tamanho(n_bytes: int) -> str:
    texto = f"{n_bytes / 1e6:.1f} MB" if n_bytes >= 1e6 else f"{n_bytes / 1e3:.0f} KB"
    return texto.replace(".", ",")


def celula_valores(nome_col: str, p: dict) -> str:
    faixa = ""
    if "minimo" in p:
        faixa = f"{md(fmt_valor(p['minimo']), 20)} a {md(fmt_valor(p['maximo']), 20)}"
        if p["distintos"] > 12:
            return faixa
    # poucos valores distintos: mostra todos, para variações de escrita ficarem visíveis
    top = p["top"] if p["distintos"] <= 12 else p["top"][:3]
    if nome_col == "email":
        top = [(mascarar_email(str(v)), n) for v, n in top]
    valores = "; ".join(f"`{md(v, 25)}` ({fmt(int(n))})" for v, n in top)
    return f"{faixa} · {valores}" if faixa else valores


def secao_arquivo(r: dict) -> list[str]:
    spec, total = r["spec"], r["total"]
    faltantes = sum(p["nulos"] + p["vazios"] + p["marcadores"] for p in r["perfis"].values())
    celulas = total * len(r["colunas"])
    info = r["info"]
    formato = "parquet" if info["formato"] == "parquet" else \
        f"CSV, separador `{info['sep']}`, {info['encoding']}{', com BOM' if info['bom'] else ''}"
    linhas = [
        f"## {r['nome']}",
        "",
        f"- **Formato:** {formato} · {tamanho((BRUTOS / r['nome']).stat().st_size)}",
        f"- **Uma linha por:** {spec['por']} (dicionário)",
        f"- **Linhas:** {fmt(total)} · dicionário: {fmt(spec['linhas'])} · "
        f"{'confere' if total == spec['linhas'] else '**diverge**'}",
        f"- **Colunas:** {len(r['colunas'])} · dicionário: {len(spec['colunas'])}",
        f"- **Células faltantes** (nulo, vazio ou marcador): {fmt(faltantes)} de {fmt(celulas)} "
        f"({pct(faltantes, celulas)})",
        f"- **Linhas duplicadas por inteiro:** {fmt(r['dup_total'])}",
        "",
        "| Coluna | Tipo (pandas) | Conteúdo | Nulos | Vazios | Marcadores | % faltante | Distintos | Faixa ou mais frequentes |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for c in r["colunas"]:
        p = r["perfis"][c]
        falta = p["nulos"] + p["vazios"] + p["marcadores"]
        linhas.append(
            f"| `{c}` | {r['palpite'].get(c, '-')} | {descrever_tipos(p['tipos'], p['n_validos'])} | "
            f"{fmt(p['nulos'])} | {fmt(p['vazios'])} | {fmt(p['marcadores'])} | {pct(falta, total)} | "
            f"{fmt(p['distintos'])} | {celula_valores(c, p)} |")
    linhas += ["", "**Divergências em relação ao dicionário**", ""]
    linhas += [f"- {d}" for d in r["div"]] or ["- Nenhuma."]
    linhas += ["", "**Observações de qualidade** (não contrariam o dicionário, mas pedem tratamento)", ""]
    linhas += [f"- {o}" for o in r["obs"]] or ["- Nenhuma."]
    linhas.append("")
    return linhas


def secao_heatmaps(hs: list[dict]) -> list[str]:
    linhas = ["## heatmaps/", "",
              "Os dois zips foram listados sem descompactar. Formato e dimensões vêm do cabeçalho de uma "
              "amostra de até 50 imagens por zip, lida direto na memória.", "",
              "| Zip | Tamanho | Arquivos | PNG | Dicionário | Pastas internas | Formato (amostra) | Tamanho por imagem |",
              "|---|---:|---:|---:|---:|---|---|---|"]
    for h in hs:
        pastas = "; ".join(f"`{p}/` ({fmt(n)})" for p, n in h["pastas"].most_common(4))
        formatos = "; ".join(f"PNG {w}×{a} px, {TIPOS_PNG.get(t, t)}, {b} bits ({n}/{h['amostra']})"
                             for (w, a, b, t), n in h["cabecalhos"].most_common(3))
        tam = f"{tamanho(min(h['tamanhos']))} a {tamanho(max(h['tamanhos']))}" if h["tamanhos"] else "-"
        linhas.append(f"| `{h['nome']}` | {tamanho(h['tamanho_zip'])} | {fmt(h['arquivos'])} | "
                      f"{fmt(h['pngs'])} | {fmt(h['esperado']) if h['esperado'] else '-'} | {pastas} | "
                      f"{formatos or '-'} | {tam} |")
    linhas += ["", "**Divergências em relação ao dicionário**", ""]
    divs = [f"- `{h['nome']}`: {d}" for h in hs for d in h["div"]]
    linhas += divs or ["- Nenhuma."]
    linhas += ["", "**Observações de qualidade**", ""]
    linhas += [f"- {o}" for h in hs for o in h["obs"]]
    linhas += ["- O dicionário chama a pasta de `heatmaps_90d/`. No data room ela se chama `heatmaps/`, "
               "e cada data vem num zip próprio.", ""]
    return linhas


def main() -> None:
    arquivos_brutos = sorted(p for p in BRUTOS.rglob("*") if p.is_file() and p.name != ".gitkeep")
    print(f"calculando hash de {len(arquivos_brutos)} arquivos...")
    hashes_antes = {p: sha256(p) for p in arquivos_brutos}

    resultados, ids_usuarios = [], None
    for nome, spec in DICIONARIO.items():
        r, ids = analisar_arquivo(nome, spec, ids_usuarios)
        if ids is not None:
            ids_usuarios = ids
        resultados.append(r)
        print(f"{nome:<25} linhas {fmt(r['total']):>10} (dicionário {fmt(spec['linhas']):>10}) · "
              f"colunas {len(r['colunas']):>2} · divergências {len(r['div'])}")

    heatmaps = [analisar_heatmaps(p, ids_usuarios) for p in sorted((BRUTOS / "heatmaps").glob("*.zip"))]
    for h in heatmaps:
        print(f"{h['nome']:<35} arquivos {fmt(h['arquivos']):>7} (dicionário {fmt(h['esperado'] or 0)}) · "
              f"divergências {len(h['div'])}")

    hashes_depois = {p: sha256(p) for p in arquivos_brutos}
    alterados = [p for p in arquivos_brutos if hashes_antes[p] != hashes_depois[p]]

    # ---- relatório ----
    out = [
        "# Inventário de dados/brutos/",
        "",
        f"Gerado em {datetime.now():%d/%m/%Y %H:%M} por `src/inventario.py`. Para gerar de novo: "
        "`.venv\\Scripts\\python src\\inventario.py`.",
        "",
        "Só leitura: nenhum arquivo bruto foi alterado (hash SHA-256 conferido antes e depois) e "
        "nenhuma limpeza foi feita. Referência: `docs/Vitaliza - Dicionário de dados.pdf`.",
        "",
        "**Como ler**",
        "",
        "- **Tipo (pandas):** o tipo que o pandas adivinharia sozinho ao ler o arquivo.",
        "- **Conteúdo:** o que os valores parecem ser, lidos como texto. Datas mostram o formato.",
        "- **Nulos:** célula sem valor (no CSV, lido como texto, quase sempre zero). "
        "**Vazios:** texto vazio ou só com espaços. "
        "**Marcadores:** textos como `null`, `NA`, `N/A`, `-`, `nan`, `none`, `?`.",
        "- **Datas** são comparadas já em horário de Brasília: valores com `Z` (UTC) são convertidos "
        "antes da comparação com o corte de 30/09/2026.",
        "- **Divergências** contrariam algo que o dicionário afirma. **Observações** são problemas de "
        "qualidade que o dicionário já avisa que existem (formatos, fusos, maiúsculas).",
        "",
        "## Resumo",
        "",
        "| Arquivo | Linhas | Dicionário | Colunas | Células faltantes | Divergências |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in resultados:
        falt = sum(p["nulos"] + p["vazios"] + p["marcadores"] for p in r["perfis"].values())
        out.append(f"| [{r['nome']}](#{r['nome'].replace('.', '')}) | {fmt(r['total'])} | "
                   f"{fmt(r['spec']['linhas'])} | {len(r['colunas'])} | "
                   f"{pct(falt, r['total'] * len(r['colunas']))} | {len(r['div'])} |")
    for h in heatmaps:
        out.append(f"| [{h['nome']}](#heatmaps) | {fmt(h['pngs'])} imagens | "
                   f"{fmt(h['esperado']) if h['esperado'] else '-'} | - | - | {len(h['div'])} |")

    out += ["", "## Divergências consolidadas", ""]
    for r in resultados:
        for d in r["div"]:
            out.append(f"- **{r['nome']}**: {d}")
    for h in heatmaps:
        for d in h["div"]:
            out.append(f"- **{h['nome']}**: {d}")
    if not any(r["div"] for r in resultados) and not any(h["div"] for h in heatmaps):
        out.append("- Nenhuma.")
    out.append("")

    for r in resultados:
        out += secao_arquivo(r)
    out += secao_heatmaps(heatmaps)

    out += ["## Integridade de dados/brutos/", ""]
    out += [f"- `{p.relative_to(BRUTOS).as_posix()}`: {'**ALTERADO**' if p in alterados else 'inalterado'} "
            f"(`{hashes_depois[p][:16]}…`)" for p in arquivos_brutos]
    out.append("")

    SAIDA.write_text("\n".join(out), encoding="utf-8")
    print(f"\nintegridade: {'OK, nada alterado' if not alterados else 'ALTERADOS: ' + str(alterados)}")
    print(f"relatório: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
