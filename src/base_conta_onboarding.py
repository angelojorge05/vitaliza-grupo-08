"""Passo 4 · base com uma linha por conta: usuarios.csv (esquerda) + onboarding padronizado.

Grava dados/processados/base_conta_onboarding.csv. Junção um-para-um validada, sem duplicar linhas.
Contas sem onboarding ficam com sem_questionario = True e os campos do questionário vazios.
Contas de teste (@vitaliza.com.br) ficam na base, marcadas em flag_conta_teste (não removidas).

Rodar da raiz:  python -I src/base_conta_onboarding.py
"""

import hashlib
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import BRUTOS, PROCESSADOS, contas_de_teste, mostrar  # noqa: E402


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def main() -> None:
    h0 = hashlib.sha256((BRUTOS / "usuarios.csv").read_bytes()).hexdigest()
    us = pd.read_csv(BRUTOS / "usuarios.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    ob = pd.read_csv(PROCESSADOS / "onboarding_padronizado.csv", dtype=str, keep_default_na=False, encoding="utf-8")
    n_us = len(mostrar("usuarios.csv", us))
    n_ob = len(mostrar("onboarding_padronizado.csv", ob))

    # grão: os dois têm um user_id por linha ANTES de juntar
    assert us["user_id"].is_unique and ob["user_id"].is_unique
    assert set(ob["user_id"]) <= set(us["user_id"]), "onboarding com user_id que não está em usuarios"

    base = us.merge(ob, on="user_id", how="left", validate="one_to_one", indicator=True)
    mostrar("junção usuarios <- onboarding (esquerda)", base, n_us)
    base["sem_questionario"] = base["_merge"].eq("left_only")
    base = base.drop(columns="_merge")

    # campos do questionário continuam vazios (texto vazio) nas contas sem onboarding
    teste = contas_de_teste()
    base["flag_conta_teste"] = base["user_id"].isin(teste)

    assert len(base) == n_us, "a junção mudou o número de linhas"
    assert base["user_id"].is_unique, "user_id duplicado depois da junção"
    assert int((~base["sem_questionario"]).sum()) == n_ob
    print(f"com questionário: {fmt(int((~base['sem_questionario']).sum()))} | sem questionário: {fmt(int(base['sem_questionario'].sum()))} "
          f"| soma {fmt(len(base))}")
    print(f"contas de teste marcadas: {fmt(int(base['flag_conta_teste'].sum()))}")
    print(f"colunas: {len(base.columns)} -> {base.columns.tolist()}")
    # as colunas de usuarios não mudaram na junção
    assert base[us.columns].equals(us), "colunas de usuarios foram alteradas"
    assert not base["email"].isna().any()

    PROCESSADOS.mkdir(parents=True, exist_ok=True)
    base.to_csv(PROCESSADOS / "base_conta_onboarding.csv", index=False, encoding="utf-8")
    mostrar("base_conta_onboarding.csv gravado", base, n_us)
    assert hashlib.sha256((BRUTOS / "usuarios.csv").read_bytes()).hexdigest() == h0
    print("hash de usuarios.csv igual antes/depois: True")


if __name__ == "__main__":
    main()
