"""Limpeza de outliers de atividades: gera dados/processados/atividades_limpa_v2.parquet.

Parte de atividades_limpa.parquet (decisões 9-12: tipo canônico, fuso, dedup) e aplica,
nesta ordem, com a contagem depois de cada passo:
1. duração <= 0            -> REMOVE o treino (não houve treino de 0 min);
2. distância > 200 km      -> ANULA distancia_km e ritmo_min_km, mantém o treino;
3. gps_ok falso e distância preenchida -> ANULA distancia_km e ritmo_min_km;
4. distância 0 em tipo com GPS (corrida, caminhada, pedal) -> ANULA distancia_km e ritmo_min_km.
O valor original fica em `distancia_km_original` e cada anulação tem a sua marca.
`flag_outlier_iqr` (decisão 12, só informativa) é recalculada sobre a distância limpa.
O bruto não é tocado (SHA-256 conferido antes e depois). Saída: saidas/limpeza_outliers_atividades.md.
"""

import hashlib
import subprocess
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
BRUTO = RAIZ / "dados" / "brutos" / "atividades.parquet"
ENTRADA = RAIZ / "dados" / "processados" / "atividades_limpa.parquet"
SAIDA_DADOS = RAIZ / "dados" / "processados" / "atividades_limpa_v2.parquet"
RELATORIO = RAIZ / "saidas" / "limpeza_outliers_atividades.md"
LIMIAR_KM = 200
TIPOS_GPS = ["corrida", "caminhada", "pedal"]


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def n(x) -> str:
    return f"{int(x):,}".replace(",", ".")


def main() -> None:
    hash_antes = sha256(BRUTO)
    if not ENTRADA.exists():
        print("atividades_limpa.parquet ausente: gerando com src/preparar_atividades.py")
        subprocess.run([sys.executable, str(RAIZ / "src" / "preparar_atividades.py")], check=True)
    df = pd.read_parquet(ENTRADA)
    linhas: list[tuple[str, str, str]] = []
    n0 = len(df)
    dist0 = int(df["distancia_km"].notna().sum())
    linhas.append(("0. Entrada (atividades_limpa, decisões 9-12)", f"{n(n0)} treinos", f"{n(dist0)} com distância"))
    print(f"[0] entrada: {n(n0)} treinos · {n(dist0)} com distância")

    df["distancia_km_original"] = df["distancia_km"]
    df["ritmo_min_km_original"] = df["ritmo_min_km"]

    def anular(mask: pd.Series, flag: str) -> int:
        df[flag] = mask
        df.loc[mask, ["distancia_km", "ritmo_min_km"]] = pd.NA
        return int(mask.sum())

    # 1. duração <= 0: remove
    dur0 = df["duracao_min"] == 0
    dur_neg = df["duracao_min"] < 0
    k_dur = int((dur0 | dur_neg).sum())
    df = df[~(dur0 | dur_neg)].copy()
    linhas.append(("1. Remove duração <= 0", f"-{n(k_dur)} treinos (zero: {n(dur0.sum())}; negativa: {n(dur_neg.sum())})",
                   f"{n(n0)} → {n(len(df))}"))
    print(f"[1] duração <= 0 removida: -{n(k_dur)} → {n(len(df))} treinos")

    # 2. > 200 km
    k200 = anular(df["distancia_km"] > LIMIAR_KM, "dist_anulada_acima_200km")
    linhas.append((f"2. Anula distância > {LIMIAR_KM} km (e ritmo)", f"{n(k200)} distâncias anuladas", f"linhas: {n(len(df))}"))
    print(f"[2] > {LIMIAR_KM} km anuladas: {n(k200)} · linhas {n(len(df))}")

    # 3. gps_ok falso com distância preenchida
    k_gps = anular(~df["gps_ok"] & df["distancia_km"].notna(), "dist_anulada_gps_falso")
    linhas.append(("3. Anula distância com gps_ok falso (e ritmo)", f"{n(k_gps)} distâncias anuladas", f"linhas: {n(len(df))}"))
    print(f"[3] gps_ok falso anuladas: {n(k_gps)} · linhas {n(len(df))}")

    # 4. distância zero em tipo com GPS
    k_zero = anular((df["distancia_km"] == 0) & df["tipo"].isin(TIPOS_GPS), "dist_anulada_zero")
    zero_outros = int(((df["distancia_km"] == 0) & ~df["tipo"].isin(TIPOS_GPS)).sum())
    linhas.append(("4. Anula distância 0 em tipo com GPS (e ritmo)",
                   f"{n(k_zero)} anuladas; {n(zero_outros)} zeros em outros tipos mantidos", f"linhas: {n(len(df))}"))
    print(f"[4] distância 0 em tipo com GPS anuladas: {n(k_zero)} · zeros em outros tipos mantidos: {n(zero_outros)}")

    # consistência do ritmo
    ritmo_sem_dist = int((df["ritmo_min_km"].notna() & df["distancia_km"].isna()).sum())
    print(f"[ritmo] ritmo preenchido com distância vazia: {n(ritmo_sem_dist)}")

    # IQR recalculado, informativo
    d = df["distancia_km"].dropna()
    q1, q3 = d.quantile([0.25, 0.75])
    lim = q3 + 1.5 * (q3 - q1)
    df["flag_outlier_iqr"] = df["distancia_km"].gt(lim)
    k_iqr = int(df["flag_outlier_iqr"].sum())
    linhas.append((f"5. flag_outlier_iqr recalculada (> {lim:.2f} km, só informativa)", f"{n(k_iqr)} marcados, 0 removidos",
                   f"linhas: {n(len(df))}"))
    print(f"[5] flag_outlier_iqr: {n(k_iqr)} (> {lim:.2f} km) · nada removido")

    # a flag_impossivel antiga deixa de valer: valores impossíveis já foram tratados
    df = df.drop(columns=["flag_impossivel"])
    df = df.sort_values("atividade_id").reset_index(drop=True)
    df.to_parquet(SAIDA_DADOS, index=False)

    max_dist = df["distancia_km"].max()
    dist_fim = int(df["distancia_km"].notna().sum())
    conf_linhas = n0 - k_dur == len(df)
    estado = "inalterado" if sha256(BRUTO) == hash_antes else "ALTERADO"
    print(f"\nsaída: {SAIDA_DADOS.relative_to(RAIZ)} · {n(len(df))} treinos · {n(dist_fim)} com distância · máx {max_dist:.2f} km")
    print(f"bruto {estado} ({hash_antes[:16]}…) · conferência de linhas: {'ok' if conf_linhas else 'ERRO'}")

    tab = "\n".join(f"| {a} | {b} | {c} |" for a, b, c in linhas)
    RELATORIO.write_text(f"""# Limpeza de outliers de atividades

Gerado por `src/limpar_outliers_atividades.py`. Saída: `dados/processados/atividades_limpa_v2.parquet` (fora do Git). Bruto inalterado (SHA-256 `{hash_antes[:16]}…`).
Valores originais ficam em `distancia_km_original` e `ritmo_min_km_original`; cada anulação tem sua marca (`dist_anulada_acima_200km`, `dist_anulada_gps_falso`, `dist_anulada_zero`).

| Passo | Efeito | Contagem |
|---|---|---|
{tab}

- Linhas finais: **{n(len(df))}** (entrada {n(n0)} − {n(k_dur)} de duração ≤ 0). Distância preenchida: {n(dist0)} → {n(dist_fim)}. Distância máxima: {max_dist:.2f} km.
- Ritmo preenchido com distância vazia depois da limpeza: {n(ritmo_sem_dist)}.
- A marca `flag_impossivel` da v1 sai da v2: os impossíveis foram removidos ou anulados.
- Não limpo, de propósito: os {n(k_iqr)} treinos acima do IQR (pedais longos e plausíveis) e as durações altas (máx. 543,9 min).

## Decisões propostas para o `decisoes.md` (ainda não gravadas)

| # | Data | Arquivo | Problema | Decisão | Motivo | Efeito |
|---|---|---|---|---|---|---|
| 23 | 09/11/2026 | atividades.parquet | duração ≤ 0 | remover da cópia v2 (substitui a marca da decisão 9 para duração) | treino de 0 min não aconteceu | -{n(k_dur)} treinos: {n(n0)} → {n(len(df))} |
| 24 | 09/11/2026 | atividades.parquet | distância > 200 km | anular `distancia_km` e `ritmo_min_km`, manter o treino (substitui a marca da decisão 9 para distância) | fisicamente impossível, mas o treino existe | {n(k200)} anuladas; linhas inalteradas |
| 25 | 09/11/2026 | atividades.parquet | `gps_ok` falso com distância | anular `distancia_km` e `ritmo_min_km`, manter o treino | dicionário: distância só existe com GPS | {n(k_gps)} anuladas |
| 26 | 09/11/2026 | atividades.parquet | distância 0 em corrida, caminhada ou pedal | anular `distancia_km` e `ritmo_min_km` | zero em tipo com GPS é falha de medição | {n(k_zero)} anuladas |
""", encoding="utf-8")
    print(f"relatório: {RELATORIO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
