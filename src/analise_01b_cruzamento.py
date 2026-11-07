"""Análise 1b: pagantes ativos no corte com TODAS as colunas de usuarios.csv. Colaborador 1.

Parte do mesmo filtro da análise 1 (ativas, sem contas de teste = 14.753) e junta usuarios.csv
inteiro pela esquerda. Valores originais são mantidos; as versões padronizadas entram em
colunas novas (sufixo _padrao) e as datas suspeitas ficam só marcadas (flags), sem remoção.
Saída: dados/processados/pagantes_ativos_corte.csv. Dados brutos não são alterados.
"""

import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from utils import BRUTOS, CORTE, DOMINIO_TESTE, PROCESSADOS, mostrar

CIDADE = {  # chave: minúsculas sem acento
    "b. horizonte": "Belo Horizonte", "bh": "Belo Horizonte", "belo horizonte": "Belo Horizonte",
    "bsb": "Brasília", "brasilia": "Brasília", "brasilia - df": "Brasília",
    "floripa": "Florianópolis", "florianopolis": "Florianópolis",
    "rio": "Rio de Janeiro", "rj": "Rio de Janeiro", "rio de janeiro": "Rio de Janeiro",
    "s. paulo": "São Paulo", "sp": "São Paulo", "sampa": "São Paulo", "sao paulo": "São Paulo",
    "sao paulo - sp": "São Paulo",
}
SEXO = {"f": "F", "fem": "F", "feminino": "F", "m": "M", "masc": "M", "masculino": "M"}
SISTEMA = {"android": "android", "ios": "ios"}


def chave(s: pd.Series) -> pd.Series:
    def f(x):
        x = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode().strip().lower()
        return x
    return s.map(f)


a = pd.read_csv(BRUTOS / "assinaturas.csv", dtype=str)
u = pd.read_csv(BRUTOS / "usuarios.csv", dtype=str, keep_default_na=False)
mostrar("assinaturas.csv", a)
mostrar("usuarios.csv", u)

n = len(a)
ativas = mostrar("ativas", a[a["status_atual"].str.strip().str.lower() == "ativa"], n)
u["teste"] = u["email"].str.strip().str.lower().str.endswith(DOMINIO_TESTE)
assert u["user_id"].is_unique

j = ativas.merge(u, on="user_id", how="left", validate="one_to_one")
mostrar("junção ativas x usuarios (todas as colunas)", j, len(ativas))
assert j["email"].notna().all(), "pagante sem conta em usuarios"
n = len(j)
p = mostrar("sem contas de teste", j[~j["teste"]].drop(columns="teste").reset_index(drop=True), n)
assert len(p) == 14_753 and p["user_id"].is_unique

# padronização em colunas novas
c = chave(p["cidade"])
desconhecidas = sorted(set(c) - set(CIDADE))
p["cidade_padrao"] = c.map(CIDADE)
p["cidade_padrao"] = p["cidade_padrao"].fillna(p["cidade"].str.strip().where(~c.isin(desconhecidas)))
for v in desconhecidas:  # cidades que já estavam corretas: mantém o texto original mais comum
    mais_comum = p.loc[c == v, "cidade"].mode().iloc[0]
    p.loc[c == v, "cidade_padrao"] = mais_comum
p["sexo_padrao"] = chave(p["sexo"]).map(SEXO)
p["sistema_padrao"] = chave(p["sistema"]).map(SISTEMA)

# datas: só marcar
cad = pd.to_datetime(p["data_cadastro"], errors="coerce")
nas = pd.to_datetime(p["data_nascimento"].replace("", pd.NA), errors="coerce")
p["flag_cadastro_apos_corte"] = cad > CORTE
p["flag_nascimento_invalido"] = (nas > CORTE) | (nas < "1920-01-01")

# relatório de conferência
print("\nlinhas:", len(p), "| colunas:", p.shape[1])
print("cidades:", p["cidade_padrao"].nunique(), "| sem mapa:", int(p["cidade_padrao"].isna().sum()))
for col in ["sexo", "sexo_padrao", "sistema", "sistema_padrao", "canal_aquisicao", "relogio_conectado"]:
    print(f"\n{col}:\n{p[col].value_counts(dropna=False).to_string()}")
print("\ncidade 'RJ'/'SP' vs uf:\n", pd.crosstab(p.loc[chave(p['cidade']).isin(['rj', 'sp']), 'cidade'], p['uf']).to_string())
print("\nflags:", p[["flag_cadastro_apos_corte", "flag_nascimento_invalido"]].sum().to_dict(),
      "| nascimento vazio:", int((p["data_nascimento"] == "").sum()))
print("\nuf x cidade_padrao (cidades por uf):\n", p.groupby("uf")["cidade_padrao"].nunique().to_string())

PROCESSADOS.mkdir(exist_ok=True)
p.to_csv(PROCESSADOS / "pagantes_ativos_corte.csv", index=False, encoding="utf-8")
print("\nSalvo:", PROCESSADOS / "pagantes_ativos_corte.csv")
