"""Unicidade em dados/brutos/atividades.parquet (prompt 04): treinos que chegaram em dobro.

Mede o deslocamento de horário de cada origem (sem supor fuso), acha os pares app x relógio
sem e com a correção e propõe, sem aplicar, qual linha manter. Só lê o bruto (SHA-256 antes e
depois); grava apenas saidas/unicidade_atividades.md.
"""

import hashlib
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "dados" / "brutos" / "atividades.parquet"
SAIDA = RAIZ / "saidas" / "unicidade_atividades.md"
MAPA = {"run": "corrida", "walk": "caminhada", "ride": "pedal", "strength": "forca"}
TOL = 5.0  # minutos
JANELA_H = 24


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def n(x) -> str:
    return f"{int(x):,}".replace(",", ".")


def tabela(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    return "\n".join([cab, sep, *("| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |"
                                  for r in df.itertuples(index=False))])


def emparelhar(cand: pd.DataFrame, delta_col: str) -> tuple[pd.DataFrame, int, int, int]:
    """Candidatos dentro da tolerância -> 1 par por treino (guloso pelo menor |delta|).
    Devolve (pares, candidatos na tolerância, treinos app repetidos, treinos relógio repetidos)."""
    dentro = cand[cand[delta_col].abs() <= TOL].copy()
    dentro["abs"] = dentro[delta_col].abs()
    rep_app = int(dentro.duplicated("atividade_id_app", keep=False).sum())
    rep_rel = int(dentro.duplicated("atividade_id_rel", keep=False).sum())
    usados_a: set = set()
    usados_r: set = set()
    manter = []
    for i, a, r in zip(dentro.sort_values("abs").index, dentro.sort_values("abs")["atividade_id_app"],
                       dentro.sort_values("abs")["atividade_id_rel"]):
        if a in usados_a or r in usados_r:
            continue
        usados_a.add(a)
        usados_r.add(r)
        manter.append(i)
    return dentro.loc[manter], len(dentro), rep_app, rep_rel


def main() -> None:
    hash_antes = sha256(ARQUIVO)
    df = pd.read_parquet(ARQUIVO, engine="pyarrow")
    df["inicio"] = pd.to_datetime(df["inicio"])
    df["tipo_canon"] = df["tipo"].map(lambda t: MAPA.get(t, t))  # cópia em memória
    total = len(df)
    app = df[df["origem"] == "app"]
    rel = df[df["origem"].isin(["garmin", "apple_health"])]
    print(f"[0] {n(total)} treinos · app {n(len(app))} · relógio {n(len(rel))}")

    out: list[str] = []
    p = out.append
    p("# Unicidade de atividades.parquet: treinos em dobro (app × relógio)\n")
    p(f"Gerado por `src/unicidade_atividades.py`. Só leitura: `atividades.parquet` com SHA-256 `{hash_antes[:16]}…` conferido antes e depois. Nada foi removido nem alterado.\n")

    # 2. deslocamento de horário (sem janela de tempo, sem supor fuso)
    cand = app.merge(rel, on=["user_id", "tipo_canon", "duracao_min"], suffixes=("_app", "_rel"))
    cand["delta_min"] = (cand["inicio_rel"] - cand["inicio_app"]).dt.total_seconds() / 60
    cand = cand[cand["delta_min"].abs() <= JANELA_H * 60].copy()
    cand["delta_h_arred"] = (cand["delta_min"] / 60).round().astype(int)
    print(f"[2] candidatos (conta+tipo+duração, |Δ| ≤ {JANELA_H} h): {n(len(cand))}")
    p("## 1. Deslocamento de horário por origem (medido, não suposto)\n")
    p(f"Candidatos: mesma conta, mesmo tipo padronizado e mesma duração, um do `app` e um do relógio, **sem limite de tempo** além de ±{JANELA_H} h: {n(len(cand))}. "
      "Para cada um, calculo `início do relógio − início do app`. Se uma origem grava o horário deslocado, os verdadeiros pares se concentram numa hora inteira; o resto se espalha.\n")
    desloc: dict[str, int] = {}
    for orig in ["garmin", "apple_health"]:
        c = cand[cand["origem_rel"] == orig]
        hist = c["delta_h_arred"].value_counts().sort_index()
        pico = int(hist.idxmax())
        desloc[orig] = pico
        # fração do pico que fica a ≤ 5 min do deslocamento exato
        no_pico = c[(c["delta_min"] - pico * 60).abs() <= TOL]
        mediana_h = no_pico["delta_min"].median() / 60 if len(no_pico) else float("nan")
        print(f"[2] {orig}: {n(len(c))} candidatos · pico em {pico:+d} h · {n(len(no_pico))} a ≤ {TOL:g} min do pico · mediana {mediana_h:+.3f} h")
        p(f"### {orig}: {n(len(c))} candidatos\n")
        h = hist.rename_axis("deslocamento (h)").reset_index(name="candidatos")
        h["candidatos"] = h["candidatos"].map(n)
        p(tabela(h[h["deslocamento (h)"].abs() <= 6]) + "\n")
        p(f"- Pico: **{pico:+d} h** ({n(hist.max())} candidatos na hora inteira); {n(len(no_pico))} candidatos ficam a ≤ {TOL:g} min de {pico:+d} h, "
          f"com mediana de **{mediana_h:+.3f} h**. Fora do pico a contagem é residual (treinos parecidos em dias diferentes).\n")

    p("**Evidência resumida:** deslocamento medido = " + "; ".join(f"`{o}` {d:+d} h" for o, d in desloc.items())
      + ". A correção abaixo usa exatamente esses valores, subtraídos do início do relógio.\n")

    # 3. pares sem e com correção
    cand["delta_sem"] = cand["delta_min"]
    cand["delta_com"] = cand["delta_min"] - cand["origem_rel"].map(desloc) * 60
    sem, n_sem, rep_a_sem, rep_r_sem = emparelhar(cand, "delta_sem")
    com, n_com, rep_a_com, rep_r_com = emparelhar(cand, "delta_com")
    print(f"[3] pares únicos sem correção: {n(len(sem))} · com correção: {n(len(com))} · diferença {n(len(com) - len(sem))}")
    p("## 2. Pares sem e com correção do deslocamento\n")
    comp = pd.DataFrame({
        "origem do relógio": ["garmin", "apple_health", "total"],
        "sem correção": [n((sem['origem_rel'] == 'garmin').sum()), n((sem['origem_rel'] == 'apple_health').sum()), n(len(sem))],
        "com correção": [n((com['origem_rel'] == 'garmin').sum()), n((com['origem_rel'] == 'apple_health').sum()), n(len(com))],
    })
    comp["diferença"] = [n(int(x.replace('.', '')) - int(y.replace('.', ''))) for x, y in zip(comp["com correção"], comp["sem correção"])]
    p(tabela(comp) + "\n")
    p("Pares = um por treino, depois de desempatar (ver seção 4).\n")

    # 4. conferências sobre os pares corrigidos
    por_orig = com["origem_rel"].value_counts()
    soma_orig = int(por_orig.sum())
    ok_soma = soma_orig == len(com)
    ids_app_rep = int(com["atividade_id_app"].duplicated().sum())
    ids_rel_rep = int(com["atividade_id_rel"].duplicated().sum())
    ok_unico = ids_app_rep == 0 and ids_rel_rep == 0
    igual = ((com["distancia_km_app"] == com["distancia_km_rel"]) |
             (com["distancia_km_app"].isna() & com["distancia_km_rel"].isna()))
    print(f"[4] por origem {dict(por_orig)} · soma {n(soma_orig)} {'ok' if ok_soma else 'ERRO'} · treinos em 2 pares: app {ids_app_rep}, relógio {ids_rel_rep}")
    print(f"[4] distância igual nos pares: {n(igual.sum())} de {n(len(com))}")
    p("## 3. Pares por origem (com correção)\n")
    t = por_orig.rename_axis("par").reset_index(name="pares")
    t["par"] = "app com " + t["par"]
    t["pares"] = t["pares"].map(n)
    p(tabela(t) + f"\n\nSoma por origem: **{n(soma_orig)}** {'= total de pares ✔' if ok_soma else '≠ total ✘'} ({n(len(com))}).\n")

    p("## 4. Distância e treinos em mais de um par\n")
    p(f"- Distância também igual (ou as duas vazias): **{n(igual.sum())}** de {n(len(com))} ({100*igual.mean():.1f}%). Diferentes: {n((~igual).sum())}.")
    p(f"- Antes de desempatar: {n(n_com)} combinações dentro de {TOL:g} min; {n(rep_a_com)} delas envolvem um treino do app que casa com mais de um do relógio e "
      f"{n(rep_r_com)} um do relógio que casa com mais de um do app. Desempate: o par de menor diferença de início, um par por treino.")
    p(f"- Depois do desempate: treinos do app em 2 pares = **{ids_app_rep}**; treinos do relógio em 2 pares = **{ids_rel_rep}** {'✔' if ok_unico else '✘'}.\n")

    # 5. cinco pares lado a lado
    amostra = pd.concat([com[com["origem_rel"] == "garmin"].sample(3, random_state=7),
                         com[com["origem_rel"] == "apple_health"].sample(2, random_state=7)])
    colunas = ["atividade_id", "user_id", "inicio", "tipo", "duracao_min", "distancia_km", "ritmo_min_km", "fc_media", "origem", "gps_ok", "treino_com"]
    p("## 5. Cinco pares lado a lado (todas as colunas; `tipo_canon` é a cópia em memória)\n")
    for k, (_, r) in enumerate(amostra.iterrows(), 1):
        chaves = ("user_id", "duracao_min")  # chaves do cruzamento: sem sufixo, iguais nos dois lados
        linhas = [[c, r[c], r[c]] if c in chaves else [c, r.get(f"{c}_app"), r.get(f"{c}_rel")] for c in colunas]
        linhas.append(["tipo_canon", r["tipo_canon"], r["tipo_canon"]])
        linhas.append(["diferença de início corrigida (min)", f"{r['delta_com']:+.1f}", ""])
        p(f"### Par {k}: app com {r['origem_rel']}\n")
        p(tabela(pd.DataFrame(linhas, columns=["coluna", "app", "relógio"])) + "\n")

    # 6. decisão proposta
    sobra_fc = int(com["fc_media_rel"].notna().sum())
    p("## 6. Decisão proposta (formato do `decisoes.md`, não gravada)\n")
    p("| # | Data | Arquivo | Problema | Decisão (corrigir/remover/marcar) | Motivo | Efeito na contagem (antes → depois) |")
    p("|---|------|---------|----------|-----------------------------------|--------|-------------------------------------|")
    p(f"| — | 09/11/2026 | atividades.parquet | {n(len(com))} treinos registrados em dobro (app × relógio): mesma conta, tipo, duração, início ≤ {TOL:g} min "
      f"com o deslocamento medido ({'; '.join(f'{o} {d:+d} h' for o, d in desloc.items())}) | remover da cópia tratada a linha do **app** de cada par e manter a do **relógio**; "
      f"marcar `duplicata_app_relogio` se preferir manter a linha | o relógio traz `fc_media` ({n(sobra_fc)} dos {n(len(com))} pares têm frequência cardíaca no relógio) e o `inicio` com origem conhecida; "
      f"{n(len(sem))} pares apareceriam sem a correção, {n(len(com) - len(sem))} ficariam de fora | {n(total)} → {n(total - len(com))} (−{n(len(com))}) |")
    p("\nNota: reproduz a lógica da decisão 11; esta é a medição independente do deslocamento.\n")

    estado = "inalterado" if sha256(ARQUIVO) == hash_antes else "ALTERADO"
    p(f"---\nConferência: {n(total)} linhas lidas, nenhuma removida; `atividades.parquet` {estado}.")
    SAIDA.write_text("\n".join(out), encoding="utf-8")
    print(f"atividades.parquet {estado} · soma por origem {'ok' if ok_soma else 'ERRO'} · nenhum treino em 2 pares {'ok' if ok_unico else 'ERRO'}")
    print(f"escrito: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
