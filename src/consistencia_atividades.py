"""Consistência de `tipo` em dados/brutos/atividades.parquet (prompt 03).

Lista os valores, confere maiúsculas/acentos/espaços, cruza com `origem`, propõe o mapa
de padronização SEM aplicar e conta as linhas afetadas. Só lê o bruto (SHA-256 antes e
depois); grava apenas saidas/consistencia_atividades.md.
"""

import hashlib
import unicodedata
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "dados" / "brutos" / "atividades.parquet"
SAIDA = RAIZ / "saidas" / "consistencia_atividades.md"
LINHAS_DICIONARIO = 1_254_475
# Proposta (não aplicada): inglês -> português, que é a forma majoritária
MAPA = {"run": "corrida", "walk": "caminhada", "ride": "pedal", "strength": "forca"}


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def n(x) -> str:
    return f"{int(x):,}".replace(",", ".")


def forma(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s.strip().lower()


def tabela(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    return "\n".join([cab, sep, *("| " + " | ".join(map(str, r)) + " |" for r in df.itertuples(index=False))])


def main() -> None:
    hash_antes = sha256(ARQUIVO)
    df = pd.read_parquet(ARQUIVO, columns=["atividade_id", "tipo", "origem"], engine="pyarrow")
    out: list[str] = []
    p = out.append
    total = len(df)
    nulos = int(df["tipo"].isna().sum())

    # 1. valores
    cont = df["tipo"].value_counts(dropna=False).rename_axis("tipo").reset_index(name="linhas")
    soma = int(cont["linhas"].sum())
    ok1 = soma == total == LINHAS_DICIONARIO
    print(f"[1] {n(total)} linhas · {len(cont)} valores de tipo · nulos {n(nulos)} · soma {n(soma)} {'ok' if ok1 else 'ERRO'}")
    cont["forma_normalizada"] = cont["tipo"].map(lambda t: forma(str(t)))
    cont["difere_da_normalizada"] = [str(a) != b for a, b in zip(cont["tipo"], cont["forma_normalizada"])]
    n_dif = int(cont["difere_da_normalizada"].sum())
    pontas = int(df["tipo"].dropna().map(lambda s: s != s.strip()).sum())
    colide = cont.groupby("forma_normalizada")["tipo"].nunique()
    colide = colide[colide > 1]
    print(f"[1] valores com maiúscula/acento/espaço fora do padrão: {n_dif} · linhas com espaço nas pontas: {n(pontas)} "
          f"· formas que colidem após normalizar: {len(colide)}")

    p("# Consistência de `tipo` em atividades.parquet\n")
    p(f"Gerado por `src/consistencia_atividades.py`. Só leitura: `atividades.parquet` com SHA-256 `{hash_antes[:16]}…` conferido antes e depois. Nada foi aplicado.\n")
    p("## 1. Valores de `tipo`\n")
    p(tabela(cont[["tipo", "linhas"]].assign(linhas=cont["linhas"].map(n))) + "\n")
    p(f"- Soma das contagens: **{n(soma)}** = total {n(total)} = dicionário {n(LINHAS_DICIONARIO)} {'✔' if ok1 else '✘'}. Valores nulos: {n(nulos)}.")
    p(f"- Valores distintos: **{len(cont)}**.")
    p(f"- Maiúsculas, acentos e espaços: {n_dif} valor(es) diferem da forma normalizada (minúsculas, sem acento, sem espaços nas pontas); "
      f"{n(pontas)} linhas com espaço nas pontas; {len(colide)} grupos que viram o mesmo valor depois de normalizar. "
      f"{'Não há variação desse tipo.' if n_dif == 0 and not len(colide) else 'Ver tabela.'}")
    p("- O dicionário só diz \"tipo de treino\", sem lista de valores; o mapa abaixo vem dos dados.\n")

    # 2. cruzamento
    cruz = pd.crosstab(df["tipo"], df["origem"])
    cruz["total"] = cruz.sum(axis=1)
    so_uma = cruz.drop(columns="total").gt(0).sum(axis=1)
    so_uma = so_uma[so_uma == 1].index.tolist()
    cruz_fmt = cruz.reset_index().astype({c: object for c in cruz.columns})
    for c in cruz.columns:
        cruz_fmt[c] = cruz[c].map(n).values
    print(f"[2] tipo × origem: soma {n(cruz['total'].sum())} · nomes que só aparecem em uma origem: {so_uma}")
    p("## 2. Tipo × origem\n")
    p(tabela(cruz_fmt) + "\n")
    p(f"Nomes que aparecem em **uma só origem**: {', '.join(f'`{t}`' for t in so_uma) if so_uma else 'nenhum'}.")
    if so_uma:
        det = {t: cruz.loc[t].drop("total")[lambda s: s > 0].index[0] for t in so_uma}
        p("Origem de cada um: " + "; ".join(f"`{t}` → {o}" for t, o in det.items()) + ".\n")

    # 3 e 4. mapa
    mapa_ok = {k: v for k, v in MAPA.items() if k in set(df["tipo"].dropna())}
    afet = df["tipo"].map(mapa_ok).notna()
    por_troca = df.loc[afet, "tipo"].value_counts()
    soma_trocas = int(por_troca.sum())
    total_afet = int(afet.sum())
    sobram = df["tipo"].map(lambda t: mapa_ok.get(t, t)).nunique()
    ok4 = soma_trocas == total_afet
    destinos_existem = all(v in set(df["tipo"]) for v in mapa_ok.values())
    print(f"[4] linhas afetadas {n(total_afet)} = soma das trocas {n(soma_trocas)} {'ok' if ok4 else 'ERRO'} · tipos {len(cont)} → {sobram}")
    p("## 3. Mapa de padronização proposto (não aplicado)\n")
    linhas_mapa = [[k, v, n(por_troca.get(k, 0)),
                    "só em " + ", ".join(sorted(df.loc[df['tipo'] == k, 'origem'].unique()))] for k, v in mapa_ok.items()]
    p(tabela(pd.DataFrame(linhas_mapa, columns=["valor atual", "valor padrão", "linhas afetadas", "onde aparece"])) + "\n")
    p("Critério: o mesmo treino escrito em inglês e em português; o português é a forma majoritária e a que o dicionário usa em `atividades_ar_livre` (corrida, caminhada e pedal)."
      f" Os destinos já existem nos dados: {'sim' if destinos_existem else 'NÃO'}.\n")
    p("Valores mantidos como estão: " + ", ".join(f"`{t}`" for t in cont['tipo'] if t not in mapa_ok) + ".")
    p("`hiit` também aparece só no `app`, mas não tem par em português nos dados (é a sigla usada nas duas línguas); por isso não entra no mapa.\n")
    p("## 4. Efeito do mapa\n")
    p(f"- Linhas afetadas: **{n(total_afet)}** ({100*total_afet/total:.1f}% de {n(total)}).")
    p(f"- Soma das linhas por troca do mapa: **{n(soma_trocas)}** {'= linhas afetadas ✔' if ok4 else '≠ linhas afetadas ✘'}.")
    p(f"- Tipos distintos: **{len(cont)} → {sobram}**. Linhas totais: {n(total)} → {n(total)} (nenhuma removida).\n")

    # 5. decisão
    p("## 5. Decisão proposta (formato do `decisoes.md`, não gravada)\n")
    p("| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |")
    p("|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|")
    trocas = ", ".join(f"{k}→{v}" for k, v in mapa_ok.items())
    p(f"| — | 09/11/2026 | atividades.parquet | `tipo` em dois idiomas: {n(total_afet)} linhas ({100*total_afet/total:.0f}%) com nome em inglês ({trocas}), "
      f"{'só na origem ' + ', '.join(sorted(df.loc[afet, 'origem'].unique())) if df.loc[afet, 'origem'].nunique() == 1 else 'em mais de uma origem'} | "
      f"corrigir na cópia tratada: aplicar o mapa e deixar o bruto intacto | mesma categoria escrita de dois jeitos; contar só `corrida` deixaria de fora as linhas `run` | "
      f"{n(total_afet)} linhas renomeadas; {len(cont)} → {sobram} tipos; 0 removidas |")
    p("\nNota: isto reproduz a decisão 10 já em vigor (`src/preparar_atividades.py`); o resultado só serve de conferência independente.\n")

    estado = "inalterado" if sha256(ARQUIVO) == hash_antes else "ALTERADO"
    p(f"---\nConferência: {n(total)} linhas lidas, nenhuma alterada; `atividades.parquet` {estado}.")
    SAIDA.write_text("\n".join(out), encoding="utf-8")
    print(f"atividades.parquet {estado} · escrito: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
