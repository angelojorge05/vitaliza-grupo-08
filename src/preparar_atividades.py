"""Gera a cópia tratada de atividades.parquet (decisões 9–12 do decisoes.md, ratificadas 08/11).

Aplica, nesta ordem, sobre dados/brutos/atividades.parquet (que permanece intacto):
1. `tipo` canônico — run→corrida, walk→caminhada, ride→pedal, strength→forca (decisão 10);
2. `inicio` em horário de Brasília — garmin grava em UTC (+3h) e é convertido;
   app e apple_health já estão em Brasília (regra do CLAUDE.md; mesmo padrão da decisão 13);
3. dedup dos pares app × relógio — mesma conta, tipo e duração, início ≤ 5 min já no
   mesmo fuso: fica o registro do RELÓGIO (traz fc_media) e sai o do app (decisão 11);
4. `flag_impossivel` — distância > 200 km ou duração ≤ 0: fica na base, mas agregados,
   correlações e features devem excluir (decisão 9);
5. `flag_outlier_iqr` — acima de Q3 + 1,5×IQR da distância: só informativa, nada sai
   (decisão 12).

Saídas:
- dados/processados/atividades_limpa.parquet (gitignored: cada colaborador regenera com
  `python src/preparar_atividades.py`);
- saidas/preparacao_atividades.md (log auditável: efeito de cada regra na contagem).
"""

import hashlib
from pathlib import Path

import pandas as pd

from utils import BRUTOS, PROCESSADOS, SAIDAS, mostrar

ORIGEM = BRUTOS / "atividades.parquet"
DESTINO = PROCESSADOS / "atividades_limpa.parquet"
LOG = SAIDAS / "preparacao_atividades.md"

MAPA_TIPO = {"run": "corrida", "walk": "caminhada", "ride": "pedal", "strength": "forca"}
LIMIAR_IMPOSSIVEL_KM = 200
TOLERANCIA_PAR = pd.Timedelta(minutes=5)
FUSO_GARMIN_HORAS = 3  # garmin grava UTC; Brasília = UTC-3


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def fmt(n) -> str:
    return f"{n:,}".replace(",", ".")


def main() -> None:
    hash_antes = sha256(ORIGEM)
    df = pd.read_parquet(ORIGEM)
    df["inicio"] = pd.to_datetime(df["inicio"])
    n0 = len(df)
    mostrar("bruto lido", df)

    # 1. tipo canônico (decisão 10) — coluna substituída
    renomeadas = int(df["tipo"].isin(MAPA_TIPO).sum())
    df["tipo"] = df["tipo"].map(lambda t: MAPA_TIPO.get(t, t))
    print(f"[tipo] {fmt(renomeadas)} linhas renomeadas para o canônico "
          f"({df['tipo'].nunique()} categorias)")

    # 2. inicio em Brasília (garmin: UTC -> -3h)
    eh_garmin = df["origem"] == "garmin"
    df.loc[eh_garmin, "inicio"] = df.loc[eh_garmin, "inicio"] - pd.Timedelta(hours=FUSO_GARMIN_HORAS)
    print(f"[fuso] {fmt(int(eh_garmin.sum()))} inícios do garmin convertidos de UTC para Brasília")

    # 3. dedup app × relógio (decisão 11) — sai o registro do app de cada par
    app = df[df["origem"] == "app"]
    relogio = df[df["origem"].isin(["garmin", "apple_health"])]
    pares = app.reset_index().merge(
        relogio.reset_index(), on=["user_id", "tipo", "duracao_min"], suffixes=("_app", "_rel"))
    pares["delta"] = (pares["inicio_app"] - pares["inicio_rel"]).abs()
    pares = pares[pares["delta"] <= TOLERANCIA_PAR]
    pares = (pares.sort_values("delta")
                  .drop_duplicates("atividade_id_app")
                  .drop_duplicates("atividade_id_rel"))
    por_origem = pares["origem_rel"].value_counts().to_dict()
    antes = len(df)
    df = df.drop(index=pares["index_app"])
    mostrar(f"após dedup (saiu o lado app de {fmt(len(pares))} pares: {por_origem})", df, antes)

    # 4. flag_impossivel (decisão 9) — marca; agregados devem excluir
    df["flag_impossivel"] = (df["distancia_km"] > LIMIAR_IMPOSSIVEL_KM) | (df["duracao_min"] <= 0)
    n_imp = int(df["flag_impossivel"].sum())
    n_dist = int((df["distancia_km"] > LIMIAR_IMPOSSIVEL_KM).sum())
    n_dur = int((df["duracao_min"] <= 0).sum())
    print(f"[flag_impossivel] {fmt(n_imp)} marcados ({fmt(n_dist)} >200 km; {fmt(n_dur)} duração ≤0; "
          f"{fmt(n_dist + n_dur - n_imp)} com os dois)")

    # 5. flag_outlier_iqr (decisão 12) — só informativa
    d = df.loc[~df["flag_impossivel"], "distancia_km"].dropna()
    q1, q3 = d.quantile([0.25, 0.75])
    limiar_iqr = q3 + 1.5 * (q3 - q1)
    df["flag_outlier_iqr"] = df["distancia_km"].gt(limiar_iqr) & ~df["flag_impossivel"]
    n_iqr = int(df["flag_outlier_iqr"].sum())
    print(f"[flag_outlier_iqr] {fmt(n_iqr)} marcados (> {limiar_iqr:.2f} km, quartis da base tratada "
          f"sem impossíveis); nada removido")

    PROCESSADOS.mkdir(parents=True, exist_ok=True)
    df = df.sort_values("atividade_id").reset_index(drop=True)
    df.to_parquet(DESTINO, index=False)
    n_agregados = int((~df["flag_impossivel"]).sum())
    print(f"\n[saída] {DESTINO.relative_to(DESTINO.parents[2])}: {fmt(len(df))} linhas "
          f"({fmt(n_agregados)} válidas para agregados)")

    estado = "inalterado" if sha256(ORIGEM) == hash_antes else "ALTERADO"
    print(f"[integridade] atividades.parquet {estado} ({hash_antes[:16]}…)")

    LOG.write_text("\n".join([
        "# Preparação de atividades_limpa.parquet (decisões 9–12, ratificadas 08/11/2026)",
        "",
        "Gerado por `src/preparar_atividades.py`. O bruto permanece intacto "
        f"(SHA-256 `{hash_antes[:16]}…` conferido antes e depois). O arquivo tratado fica em "
        "`dados/processados/` (fora do Git): cada colaborador o regenera rodando o script.",
        "",
        "| Passo | Regra (decisão) | Efeito |",
        "|---|---|---|",
        f"| 0 | Bruto lido | {fmt(n0)} treinos |",
        f"| 1 | `tipo` canônico (10) | {fmt(renomeadas)} renomeadas; 11 → {df['tipo'].nunique()} categorias |",
        f"| 2 | `inicio` em Brasília | {fmt(int(eh_garmin.sum()))} inícios do garmin: UTC → −3h |",
        f"| 3 | Dedup app × relógio (11) | −{fmt(len(pares))} registros do app; fica o do relógio (traz `fc_media`): {fmt(n0)} → {fmt(len(df))} |",
        f"| 4 | `flag_impossivel` (9) | {fmt(n_imp)} marcados ({fmt(n_dist)} >200 km, {fmt(n_dur)} duração ≤0); agregados usam {fmt(n_agregados)} |",
        f"| 5 | `flag_outlier_iqr` (12) | {fmt(n_iqr)} marcados (> {limiar_iqr:.2f} km); nada removido |",
        "",
        "**Regra de uso:** toda análise, agregado ou feature por usuário parte de "
        "`atividades_limpa.parquet` filtrando `~flag_impossivel`; `flag_outlier_iqr` é "
        "informativa (os treinos longos de pedal são reais e ficam).",
    ]) + "\n", encoding="utf-8")
    print(f"[log] {LOG.relative_to(LOG.parents[1])}")


if __name__ == "__main__":
    main()
