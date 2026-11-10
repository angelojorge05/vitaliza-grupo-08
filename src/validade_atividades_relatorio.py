"""Validade de dados/brutos/atividades.parquet (prompt 02): distância e duração impossíveis.

Vazio, zero e valor impossível são três casos separados. Só lê o arquivo (hash
SHA-256 antes e depois); grava apenas saidas/validade_atividades.md.
"""

import hashlib
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "dados" / "brutos" / "atividades.parquet"
SAIDA = RAIZ / "saidas" / "validade_atividades.md"
LINHAS_DICIONARIO = 1_254_475
LIMIAR_KM = 200
MAPA = {"run": "corrida", "walk": "caminhada", "ride": "pedal", "strength": "forca"}


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def n(x) -> str:
    return f"{int(x):,}".replace(",", ".")


def g(x) -> str:
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tabela(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    linhas = ["| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |"
              for r in df.itertuples(index=False)]
    return "\n".join([cab, sep, *linhas])


def main() -> None:
    hash_antes = sha256(ARQUIVO)
    df = pd.read_parquet(ARQUIVO, engine="pyarrow")
    out: list[str] = []
    p = out.append

    # 1. contagens
    total = len(df)
    preench = int(df["distancia_km"].notna().sum())
    vazios = int(df["distancia_km"].isna().sum())
    ok1 = preench + vazios == total == LINHAS_DICIONARIO
    print(f"[1] treinos {n(total)} · distância preenchida {n(preench)} + vazia {n(vazios)}")
    p("# Validade de atividades.parquet: distância e duração\n")
    p("## 1. Contagens\n")
    p(f"- Treinos: **{n(total)}** (dicionário: {n(LINHAS_DICIONARIO)}).")
    p(f"- `distancia_km` preenchida: **{n(preench)}** ({100*preench/total:.1f}%); vazia: **{n(vazios)}** "
      f"({100*vazios/total:.1f}%). Vazio não é erro: a distância só existe quando há GPS.")
    p(f"- Conferência: {n(preench)} + {n(vazios)} = {n(preench+vazios)} "
      f"{'= total ✔' if ok1 else '≠ total ✘'}.\n")

    # 2. mín / mediana / máx entre os preenchidos
    p("## 2. Mínimo, mediana e máximo (só entre os preenchidos)\n")
    linhas = []
    for col in ("distancia_km", "duracao_min"):
        s = df[col].dropna()
        linhas.append([col, n(len(s)), g(s.min()), g(s.median()), g(s.max())])
        print(f"[2] {col}: n={n(len(s))} mín={s.min():g} mediana={s.median():g} máx={s.max():g}")
    p(tabela(pd.DataFrame(linhas, columns=["coluna", "preenchidos", "mínimo", "mediana", "máximo"])) + "\n")

    # 3. três casos separados
    d = df["distancia_km"]
    u = df["duracao_min"]
    acima = df[d > LIMIAR_KM]
    dist_zero = int((d == 0).sum())
    dist_neg = int((d < 0).sum())
    dur_vazia = int(u.isna().sum())
    dur_zero = int((u == 0).sum())
    dur_neg = int((u < 0).sum())
    print(f"[3] > {LIMIAR_KM} km: {n(len(acima))} · dist zero {n(dist_zero)} · dist negativa {n(dist_neg)} "
          f"· dur vazia {n(dur_vazia)} · dur zero {n(dur_zero)} · dur negativa {n(dur_neg)}")
    p("## 3. Vazio, zero e impossível (casos separados)\n")
    p(tabela(pd.DataFrame([
        ["distancia_km", "vazio (sem GPS)", n(vazios)],
        ["distancia_km", "zero", n(dist_zero)],
        ["distancia_km", "negativa", n(dist_neg)],
        ["distancia_km", f"> {LIMIAR_KM} km (impossível)", n(len(acima))],
        ["duracao_min", "vazia", n(dur_vazia)],
        ["duracao_min", "zero", n(dur_zero)],
        ["duracao_min", "negativa", n(dur_neg)],
    ], columns=["coluna", "caso", "treinos"])) + "\n")

    # 4. acima de 200 km por tipo e por origem
    por_tipo = acima["tipo"].value_counts()
    por_origem = acima["origem"].value_counts()
    ok4 = int(por_tipo.sum()) == len(acima) == int(por_origem.sum())
    print(f"[4] por tipo soma {n(por_tipo.sum())} · por origem soma {n(por_origem.sum())} · total {n(len(acima))}")
    p(f"## 4. Treinos acima de {LIMIAR_KM} km por tipo e por origem\n")
    p("Por tipo (como gravado; `run`/`corrida` etc. são o mesmo tipo em inglês e português):\n")
    p(tabela(por_tipo.rename_axis("tipo").reset_index(name="treinos")) + f"\n\nSoma: {n(por_tipo.sum())}.\n")
    canon = acima["tipo"].map(lambda t: MAPA.get(t, t)).value_counts()
    p("Por tipo, forma canônica:\n")
    p(tabela(canon.rename_axis("tipo").reset_index(name="treinos")) + "\n")
    p("Por origem:\n")
    p(tabela(por_origem.rename_axis("origem").reset_index(name="treinos")) + f"\n\nSoma: {n(por_origem.sum())}.\n")
    p(f"Conferência: tipo = origem = {n(len(acima))} {'✔' if ok4 else '✘'}.\n")

    # 5. cinco mais longos
    p("## 5. Os cinco treinos de maior distância (todas as colunas)\n")
    p(tabela(df.nlargest(5, "distancia_km")) + "\n")
    p("## 5b. Os cinco treinos de maior duração (todas as colunas)\n")
    p(tabela(df.nlargest(5, "duracao_min")) + "\n")

    # 6. gps_ok verdadeiro com distância vazia
    gps_vazio = df[df["gps_ok"] & d.isna()]
    gps_cheia_falso = int((~df["gps_ok"] & d.notna()).sum())
    print(f"[6] gps_ok verdadeiro e distância vazia: {n(len(gps_vazio))} · gps_ok falso e distância preenchida: {n(gps_cheia_falso)}")
    p("## 6. `gps_ok` x distância\n")
    p(tabela(pd.crosstab(df["gps_ok"], d.notna().map({True: "distância preenchida", False: "distância vazia"}))
             .rename_axis("gps_ok").reset_index()) + "\n")
    p(f"- `gps_ok` verdadeiro e distância vazia: **{n(len(gps_vazio))}**.")
    p(f"- `gps_ok` falso e distância preenchida: **{n(gps_cheia_falso)}**.\n")
    p("Treinos com `gps_ok` verdadeiro e distância vazia, por tipo:\n")
    p(tabela(gps_vazio["tipo"].map(lambda t: MAPA.get(t, t)).value_counts()
             .rename_axis("tipo").reset_index(name="treinos")) + "\n")

    # 7. decisões propostas
    p("## 7. Decisões propostas (não aplicadas)\n")
    p("| # | Problema | Decisão | Motivo | Efeito na contagem |")
    p("|---|---|---|---|---|")
    p(f"| a | `distancia_km` > {LIMIAR_KM} km | marcar (`flag_dist_impossivel`) e excluir dos agregados de engajamento; manter o bruto | "
      f"fisicamente impossível; remover apagaria a atividade do histórico | {n(len(acima))} marcados; linhas: {n(total)} → {n(total)} |")
    p(f"| b | `distancia_km` vazia | manter vazia, sem marca de erro | dicionário: só existe com GPS | {n(vazios)} vazios, 0 alterados |")
    p(f"| c | `distancia_km` zero ou negativa | {'marcar' if dist_zero + dist_neg else 'nada a fazer'} | "
      f"zero: {n(dist_zero)}; negativa: {n(dist_neg)} | {n(dist_zero + dist_neg)} afetados |")
    p(f"| d | `duracao_min` zero ou negativa | {'marcar (`flag_dur_invalida`)' if dur_zero + dur_neg else 'nada a fazer'} | "
      f"zero: {n(dur_zero)}; negativa: {n(dur_neg)}; duração vazia: {n(dur_vazia)} | {n(dur_zero + dur_neg)} afetados |")
    tipos_vazio = ", ".join(sorted(gps_vazio["tipo"].map(lambda t: MAPA.get(t, t)).unique()))
    p(f"| e | `gps_ok` verdadeiro e distância vazia | nada a fazer (não é problema) | todos são treinos sem percurso ({tipos_vazio}); vazio esperado | {n(len(gps_vazio))} mantidos, 0 marcados |")
    p(f"| f | `gps_ok` falso e distância preenchida | marcar (`flag_gps_falso_com_distancia`) para conferir | distância gravada sem GPS confiável; não dá para provar erro | {n(gps_cheia_falso)} marcados; linhas inalteradas |")
    p("\nNenhuma decisão foi escrita em `decisoes.md`; depende da sua aprovação.\n")

    depois = sha256(ARQUIVO)
    estado = "inalterado" if depois == hash_antes else "ALTERADO"
    p(f"---\nConferência: {n(total)} linhas lidas e nenhuma removida; `atividades.parquet` {estado} (SHA-256 `{hash_antes[:16]}…`).")
    SAIDA.write_text("\n".join(out), encoding="utf-8")
    print(f"atividades.parquet {estado} · conferências: soma={'ok' if ok1 else 'ERRO'}, grupos={'ok' if ok4 else 'ERRO'}")
    print(f"escrito: {SAIDA}")


if __name__ == "__main__":
    main()
