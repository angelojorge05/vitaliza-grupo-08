"""Análise 5 · Unicidade em dados/brutos/atividades.parquet (Colaborador 2).

Treinos que chegaram duas vezes: um registro pelo app e outro pelo relógio
(garmin ou apple_health), da mesma conta, mesmo tipo e mesma duração, com
início a até 5 minutos de distância.

Tratamento de horário por origem (regra do CLAUDE.md: converter UTC -> Brasília):
- `garmin` grava o início em UTC, 3 horas à frente -> subtrai 3h antes de comparar;
- `app` e `apple_health` já gravam em horário de Brasília -> como estão.

Tipo comparado na forma canônica (run->corrida etc., análise 4), porque o
app grava 30% dos treinos com o nome em inglês e o relógio em português.

Nada é removido nem alterado: só contagem (hash SHA-256 antes e depois).
Roteiro: docs/analises_por_colaborador/colaborador_2.md, análise 5.
"""

import hashlib
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO = RAIZ / "dados" / "brutos" / "atividades.parquet"
MAPA = {"run": "corrida", "walk": "caminhada", "ride": "pedal", "strength": "forca"}
TOLERANCIA = pd.Timedelta(minutes=5)


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def fmt(n) -> str:
    return f"{n:,}".replace(",", ".")


def main() -> None:
    hash_antes = sha256(ARQUIVO)
    cols = ["atividade_id", "user_id", "inicio", "tipo", "duracao_min", "distancia_km", "origem"]
    df = pd.read_parquet(ARQUIVO, columns=cols)
    df["inicio"] = pd.to_datetime(df["inicio"])
    print(f"treinos lidos: {fmt(len(df))}")

    # horário comparável (Brasília): garmin vem em UTC, 3h à frente
    df["inicio_brt"] = df["inicio"].where(df["origem"] != "garmin",
                                          df["inicio"] - pd.Timedelta(hours=3))
    df["tipo_canon"] = df["tipo"].map(lambda t: MAPA.get(t, t))

    app = df[df["origem"] == "app"]
    relogio = df[df["origem"].isin(["garmin", "apple_health"])]
    print(f"origem app: {fmt(len(app))} · origem relógio (garmin+apple_health): {fmt(len(relogio))}")

    # candidatos: mesma conta, mesmo tipo canônico, mesma duração
    pares = app.merge(relogio, on=["user_id", "tipo_canon", "duracao_min"],
                      suffixes=("_app", "_rel"))
    print(f"candidatos (conta + tipo + duração iguais): {fmt(len(pares))}")

    # início a até 5 minutos, já em horário comparável
    pares["delta_min"] = (pares["inicio_brt_app"] - pares["inicio_brt_rel"]).abs()
    pares = pares[pares["delta_min"] <= TOLERANCIA]
    print(f"com início a até 5 min (fuso corrigido): {fmt(len(pares))}")

    # 1 par por registro: cada treino entra em no máximo um par
    pares = (pares.sort_values("delta_min")
                  .drop_duplicates("atividade_id_app")
                  .drop_duplicates("atividade_id_rel"))
    print(f"pares únicos: {fmt(len(pares))}")

    print("\n=== 2. pares por origem do relógio ===")
    print(pares["origem_rel"].value_counts().to_string())

    dist_igual = (pares["distancia_km_app"] == pares["distancia_km_rel"]) | (
        pares["distancia_km_app"].isna() & pares["distancia_km_rel"].isna())
    print(f"\npares com a mesma distância também: {fmt(int(dist_igual.sum()))} de {fmt(len(pares))}")

    # sem a correção de fuso, quantos apareceriam?
    sem_fuso = app.merge(relogio, on=["user_id", "tipo_canon", "duracao_min"], suffixes=("_app", "_rel"))
    sem_fuso = sem_fuso[(sem_fuso["inicio_app"] - sem_fuso["inicio_rel"]).abs() <= TOLERANCIA]
    sem_fuso = (sem_fuso.assign(d=(sem_fuso["inicio_app"] - sem_fuso["inicio_rel"]).abs())
                        .sort_values("d").drop_duplicates("atividade_id_app").drop_duplicates("atividade_id_rel"))
    print(f"(armadilha) sem corrigir o fuso do garmin: {fmt(len(sem_fuso))} pares — "
          + sem_fuso["origem_rel"].value_counts().to_dict().__str__())

    print("\n=== 3. cinco pares lado a lado ===")
    mostra = pares.head(5)[["user_id", "tipo_app", "tipo_rel", "duracao_min",
                            "inicio_app", "inicio_rel", "inicio_brt_rel",
                            "distancia_km_app", "distancia_km_rel", "origem_rel", "delta_min"]]
    with pd.option_context("display.width", 220, "display.max_columns", None):
        print(mostra.to_string(index=False))

    estado = "inalterado" if sha256(ARQUIVO) == hash_antes else "ALTERADO"
    print(f"\natividades.parquet {estado} ({hash_antes[:16]}…)")


if __name__ == "__main__":
    main()
