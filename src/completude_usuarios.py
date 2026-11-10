"""Completude e duplicatas de dados/brutos/usuarios.csv (só leitura).

Lê em texto puro (dtype=str, keep_default_na=False). Grava apenas saidas/completude_usuarios.md.
Dicionário (seção 02): nenhuma coluna é marcada como "opcional". A única que admite ausência
pelo texto é relogio_conectado ("relógio conectado à conta, se houver").

Rodar da raiz:  python -I src/completude_usuarios.py
"""

import hashlib
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import BRUTOS, SAIDAS, mostrar  # noqa: E402

LINHAS_DICIONARIO = 64_948
AUSENCIA_PELO_TEXTO = {"relogio_conectado": "sim (\"se houver\")"}


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.1f}%".replace(".", ",")


def main() -> None:
    arq = BRUTOS / "usuarios.csv"
    h0 = hashlib.sha256(arq.read_bytes()).hexdigest()
    df = pd.read_csv(arq, dtype=str, keep_default_na=False, encoding="utf-8")
    n = len(mostrar("usuarios.csv", df))
    assert n == LINHAS_DICIONARIO

    # duplicatas
    dup_id = int(df["user_id"].duplicated().sum())
    email_norm = df["email"].str.strip().str.lower()
    dup_email = int((email_norm[email_norm != ""].duplicated()).sum())
    dup_linha = int(df.duplicated().sum())
    print(f"user_id únicos {fmt(df['user_id'].nunique())} | duplicados: user_id {dup_id}, e-mail {dup_email}, linha inteira {dup_linha}")

    # e-mail repetido: mesma pessoa em duas contas? (só difere por caixa/espaço)
    rep = df[email_norm.duplicated(keep=False) & (email_norm != "")].copy()
    rep["e"] = email_norm[rep.index]
    n_pares = int(rep["e"].nunique())
    so_caixa = int((df["email"].duplicated(keep=False)).sum())  # repetição no texto bruto
    mesmo_perfil = int(rep.groupby("e").apply(
        lambda g: g[["data_nascimento", "sexo", "cidade"]].drop_duplicates().shape[0] == 1, include_groups=False).sum())
    ass = pd.read_csv(BRUTOS / "assinaturas.csv", dtype=str, keep_default_na=False, usecols=["user_id"])
    contas_ass = int(rep["user_id"].isin(ass["user_id"]).sum())
    print(f"e-mail repetido (normalizado): {fmt(n_pares)} e-mails em {fmt(len(rep))} contas | repetição no texto bruto: {so_caixa} | "
          f"pares com mesmo nascimento/sexo/cidade: {fmt(mesmo_perfil)} | contas com assinatura: {fmt(contas_ass)}")
    assert so_caixa == 0 and len(rep) == 2 * n_pares

    linhas = []
    for col in df.columns:
        s = df[col]
        nulos = int((s == "").sum())
        so_esp = int(((s != "") & (s.str.strip() == "")).sum())
        linhas.append(dict(coluna=col, nulos=nulos, so_espacos=so_esp, vazios=nulos + so_esp))
    t = pd.DataFrame(linhas).sort_values(["vazios", "coluna"], ascending=[False, True]).reset_index(drop=True)
    for col in df.columns:
        assert int((df[col].str.strip() == "").sum()) == int(t.loc[t.coluna == col, "vazios"].iloc[0])
    assert len(df) == n
    assert hashlib.sha256(arq.read_bytes()).hexdigest() == h0

    print("coluna              nulos  só_espaços  vazios      %")
    for r in t.itertuples():
        print(f"{r.coluna:<18}{r.nulos:>7}{r.so_espacos:>12}{r.vazios:>8}{pct(r.vazios, n):>8}")

    cel = df.size
    vaz = int(t["vazios"].sum())
    sem_rel = t[t.coluna != "relogio_conectado"]
    cel2 = n * len(sem_rel)
    vaz2 = int(sem_rel["vazios"].sum())
    comp_linha = int((~df.apply(lambda s: s.str.strip() == "").drop(columns="relogio_conectado").any(axis=1)).sum())
    print(f"células preenchidas: {pct(cel - vaz, cel)} (todas as colunas) | {pct(cel2 - vaz2, cel2)} (sem relogio_conectado)")
    print(f"contas sem vazio fora de relogio_conectado: {fmt(comp_linha)} ({pct(comp_linha, n)})")
    rel = df["relogio_conectado"].replace("", "(vazio)").value_counts().to_dict()
    print("relogio_conectado:", rel)

    L = ["# Completude e duplicatas do usuarios.csv", "",
         "Código: `src/completude_usuarios.py`. Leitura em texto puro; só leitura (SHA-256 igual antes e depois).", "",
         "## Linhas e duplicatas", "",
         f"- Linhas: **{fmt(n)}** (dicionário: {fmt(LINHAS_DICIONARIO)}); `user_id` únicos: {fmt(df['user_id'].nunique())}.",
         f"- Duplicadas: `user_id` **{fmt(dup_id)}**, e-mail (sem diferenciar caixa) **{fmt(dup_email)}**, linha inteira **{fmt(dup_linha)}**.", "",
         "## Vazios por coluna (da mais vazia para a menos vazia)", "",
         "| Coluna | Nulos | Só espaço | Vazios | % | Ausência permitida pelo dicionário |", "|---|---:|---:|---:|---:|---|"]
    for r in t.itertuples():
        L.append(f"| `{r.coluna}` | {fmt(r.nulos)} | {fmt(r.so_espacos)} | {fmt(r.vazios)} | {pct(r.vazios, n)} | "
                 f"{AUSENCIA_PELO_TEXTO.get(r.coluna, 'não indicada')} |")
    L += ["", f"Em cada coluna, nulos + só espaço = vazios. Linhas: {fmt(n)} antes e depois.", "",
          "## Completude", "",
          f"- Células preenchidas (todas as colunas): **{pct(cel - vaz, cel)}**.",
          f"- Sem contar `relogio_conectado` (que não tem vazios): **{pct(cel2 - vaz2, cel2)}**.",
          f"- Contas sem nenhum vazio nas outras 11 colunas: {fmt(comp_linha)} ({pct(comp_linha, n)}).", "",
          "## E-mail repetido (possível pessoa em duas contas)", "",
          f"- Nenhum e-mail se repete no texto bruto, mas **{fmt(n_pares)} e-mails** aparecem em duas contas depois de ignorar maiúsculas e minúsculas "
          f"(**{fmt(len(rep))} contas**, 2 por e-mail), por exemplo `aline.campos28@gmail.com` e `ALINE.CAMPOS28@GMAIL.COM`.",
          f"- Em {fmt(mesmo_perfil)} desses e-mails as duas contas têm a mesma data de nascimento, sexo e cidade; as datas de cadastro são diferentes.",
          f"- {fmt(contas_ass)} dessas contas têm assinatura em `assinaturas.csv`; nenhuma é conta de teste.",
          "- **Não removi nem juntei nada.** Cada `user_id` tem o seu onboarding, assinaturas e treinos; juntar contas exige uma regra que o dicionário não dá. "
          "Proposta: **marcar** (`flag_email_repetido`) e decidir depois, com o grupo, se as duas contas contam como uma pessoa.", "",
          "## O que o dicionário não diz", "",
          "- Nenhuma coluna de `usuarios.csv` é marcada como opcional. `relogio_conectado` admite ausência (\"se houver\"), mas não tem nenhum vazio: "
          "a ausência vem escrita como `nenhum` (40.159 contas), contra 13.403 `garmin` e 11.386 `apple_watch`.",
          "- O dicionário afirma que os campos digitados pela pessoa (`data_nascimento`, `sexo`, `cidade`, `uf`, `cep_prefixo`) não passam por validação, "
          "mas não diz se podem ficar em branco. Por isso os vazios dessas colunas ficam como **lacuna a decidir**, e não como problema confirmado.",
          "- Os valores impossíveis (datas fora do corte) e as grafias de `sexo`, `sistema` e `cidade` já foram tratados para os pagantes "
          "nas decisões 2 a 6. Este relatório cobre as 64.948 contas só quanto a vazios e duplicatas.", ""]
    SAIDAS.mkdir(exist_ok=True)
    (SAIDAS / "completude_usuarios.md").write_text("\n".join(L), encoding="utf-8")
    print("gravado saidas/completude_usuarios.md")


if __name__ == "__main__":
    main()
