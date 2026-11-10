"""Completude de dados/brutos/onboarding.csv (Análise 2, conferência independente).

Só lê o arquivo bruto; grava apenas saidas/completude_onboarding.md.
Leitura em texto puro (dtype=str, keep_default_na=False): "NA", "-" e espaços ficam como vieram.

Opcional (dicionário, seção 10, tabela de colunas): objetivo_texto e como_conheceu.
Decisão do usuário (09/11/2026): como_conheceu conta como opcional.

Rodar da raiz do projeto:  python -I src/completude_onboarding.py
"""

import hashlib
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import BRUTOS, SAIDAS, mostrar  # noqa: E402

ARQUIVO = BRUTOS / "onboarding.csv"
LINHAS_DICIONARIO = 63_929
OPCIONAIS = {"objetivo_texto", "como_conheceu"}
COM_TRACO = ["objetivo_texto", "como_conheceu"]
# decisões já registradas pelo colega (decisoes.md 7 e 8), para conferir
COLEGA_VAZIOS = {"nivel": 4513, "dias_por_semana": 6368}
COLEGA_TRACO = {"objetivo_texto": 1322, "como_conheceu": 1190}


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.1f}%".replace(".", ",")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    hash_antes = sha256(ARQUIVO)
    df = pd.read_csv(ARQUIVO, dtype=str, keep_default_na=False, encoding="utf-8")
    total = mostrar("onboarding.csv", df).shape[0]
    assert total == LINHAS_DICIONARIO, f"dicionário diz {LINHAS_DICIONARIO}, veio {total}"

    ids = df["user_id"]
    print(f"user_id únicos: {fmt(ids.nunique())} | repetidos: {fmt(int(ids.duplicated(keep=False).sum()))} linhas")
    print(f"exemplo de acento: {df.loc[3, 'objetivo_texto']!r}")

    linhas = []
    for col in df.columns:
        s = df[col]
        nulos = int((s == "").sum())
        so_esp = int(((s != "") & (s.str.strip() == "")).sum())
        traco = int((s.str.strip() == "-").sum()) if col in COM_TRACO else 0
        linhas.append(dict(coluna=col, nulos=nulos, so_espacos=so_esp, vazios=nulos + so_esp,
                           traco=traco, opcional=col in OPCIONAIS))
    t = pd.DataFrame(linhas).sort_values(["vazios", "coluna"], ascending=[False, True]).reset_index(drop=True)

    # verificações de "pronto"
    assert (t["vazios"] == t["nulos"] + t["so_espacos"]).all()
    for col in df.columns:
        s = df[col]
        assert int((s.str.strip() == "").sum()) == int(t.loc[t.coluna == col, "vazios"].iloc[0])
    assert len(df) == total
    hash_depois = sha256(ARQUIVO)
    assert hash_antes == hash_depois, "o arquivo bruto mudou!"

    print("\ncoluna            nulos  só_espaços  vazios       %   traço  opcional")
    for r in t.itertuples():
        print(f"{r.coluna:<16}{r.nulos:>7}{r.so_espacos:>12}{r.vazios:>8}{pct(r.vazios, total):>8}{r.traco:>8}  {'sim' if r.opcional else 'não'}")

    # ausentes com e sem o traço (opcionais com marcador)
    aus = []
    for col in COM_TRACO:
        v = int(t.loc[t.coluna == col, "vazios"].iloc[0])
        tr = int(t.loc[t.coluna == col, "traco"].iloc[0])
        aus.append((col, v, tr, v + tr))
        print(f"{col}: vazios {fmt(v)} | traço {fmt(tr)} | ausentes sem traço {fmt(v)} ({pct(v, total)}) | com traço {fmt(v + tr)} ({pct(v + tr, total)})")

    # conferência com o colega
    print("\nconferência com decisoes.md 7 e 8:")
    div = []
    for col, ref in COLEGA_VAZIOS.items():
        v = int(t.loc[t.coluna == col, "vazios"].iloc[0])
        ok = v == ref
        print(f"  {col} vazios: {fmt(v)} vs {fmt(ref)} -> {'ok' if ok else 'DIVERGE'}")
        if not ok:
            div.append(col)
    for col, ref in COLEGA_TRACO.items():
        v = int(t.loc[t.coluna == col, "traco"].iloc[0])
        ok = v == ref
        print(f"  {col} traço: {fmt(v)} vs {fmt(ref)} -> {'ok' if ok else 'DIVERGE'}")
        if not ok:
            div.append(col)

    obrigatorias_vazias = t[(~t["opcional"]) & (t["vazios"] > 0)]
    print("\nnão opcionais com vazio:", obrigatorias_vazias["coluna"].tolist() or "nenhuma")
    print(f"hash do bruto igual antes/depois: {hash_antes == hash_depois} | linhas {total} -> {len(df)}")

    # ---- relatório ----
    L = ["# Completude do onboarding.csv (Análise 2, conferência independente)", "",
         "Código: `src/completude_onboarding.py`. Leitura em texto puro (`dtype=str`, `keep_default_na=False`). "
         "Nada em `dados/brutos/` foi alterado (SHA-256 igual antes e depois).", "",
         "## Linhas", "",
         f"- Linhas: **{fmt(total)}** (dicionário: {fmt(LINHAS_DICIONARIO)}).",
         f"- `user_id` únicos: **{fmt(ids.nunique())}**; linhas com `user_id` repetido: {fmt(int(ids.duplicated(keep=False).sum()))}.", "",
         "## Vazios por coluna (da mais vazia para a menos vazia)", "",
         "| Coluna | Nulos | Só espaço | Vazios | % das linhas | Traço `-` | Opcional (dicionário) |",
         "|---|---:|---:|---:|---:|---:|---|"]
    for r in t.itertuples():
        L.append(f"| `{r.coluna}` | {fmt(r.nulos)} | {fmt(r.so_espacos)} | {fmt(r.vazios)} | {pct(r.vazios, total)} | "
                 f"{fmt(r.traco) if r.coluna in COM_TRACO else '—'} | {'sim' if r.opcional else 'não'} |")
    L += ["", f"Soma conferida: em cada coluna, nulos + só espaço = vazios, e o total de linhas ({fmt(total)}) é o mesmo antes e depois.", "",
          "## Traço `-` como ausência (colunas opcionais)", "",
          "| Coluna | Vazios | Traço | Ausentes sem o traço | Ausentes com o traço |", "|---|---:|---:|---:|---:|"]
    for col, v, tr, tot in aus:
        L.append(f"| `{col}` | {fmt(v)} | {fmt(tr)} | {fmt(v)} ({pct(v, total)}) | {fmt(tot)} ({pct(tot, total)}) |")
    L += ["", "## O que o dicionário diz (seção 10)", "",
          "- A tabela de colunas marca `objetivo_texto` e `como_conheceu` como opcionais. Não são opcionais: `onboarding_id`, `user_id`, `respondido_em`, `nivel` e `dias_por_semana`.",
          "- **Ressalva:** o texto da seção diz só que \"o objetivo é opcional\". Por decisão do usuário (09/11/2026), `como_conheceu` foi tratada como opcional, como na tabela.",
          "- O dicionário não diz que `nivel` e `dias_por_semana` possam ficar sem resposta; por isso o vazio ali é problema.", "",
          "## Conferência com o colega (decisões 7 e 8)", ""]
    for col, ref in COLEGA_VAZIOS.items():
        v = int(t.loc[t.coluna == col, "vazios"].iloc[0])
        L.append(f"- `{col}` vazios: {fmt(v)} (colega: {fmt(ref)}) → {'confere' if v == ref else 'DIVERGE'}")
    for col, ref in COLEGA_TRACO.items():
        v = int(t.loc[t.coluna == col, "traco"].iloc[0])
        L.append(f"- `{col}` traço: {fmt(v)} (colega: {fmt(ref)}) → {'confere' if v == ref else 'DIVERGE'}")
    L += ["", "## Decisões propostas (não aplicadas; formato do `decisoes.md`)", "",
          "| # | Data | Arquivo | Problema | Decisão | Motivo | Efeito na contagem |", "|---|---|---|---|---|---|---|"]
    for r in obrigatorias_vazias.itertuples():
        L.append(f"| a definir | 09/11/2026 | onboarding.csv | Vazios em `{r.coluna}` (campo não opcional): {fmt(r.vazios)} ({pct(r.vazios, total)}) | "
                 f"marcar (`{r.coluna}_nao_informado`, mantendo o valor original vazio) | o dicionário não marca a coluna como opcional, então o vazio é lacuna real; "
                 f"não há valor certo para corrigir, e remover perderia contas com o resto da resposta | {fmt(total)} → {fmt(total)} (0 removidas; {fmt(r.vazios)} marcadas) |")
    if obrigatorias_vazias.empty:
        L.append("| — | — | — | Nenhuma coluna não opcional com vazio | — | — | — |")
    L.append("")
    SAIDAS.mkdir(exist_ok=True)
    (SAIDAS / "completude_onboarding.md").write_text("\n".join(L), encoding="utf-8")
    print("\nrelatório gravado em saidas/completude_onboarding.md")


if __name__ == "__main__":
    main()
