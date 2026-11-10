"""Análise 1: pagantes ativos no corte (30/09/2026). Colaborador 1.

Arquivos: assinaturas.csv e usuarios.csv (só leitura).
Saída: saidas/pagantes_ativos_corte.md. Referência do case: 14.753.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from utils import BRUTOS, CORTE, DOMINIO_TESTE, SAIDAS, mostrar, para_brasilia

etapas = []


def etapa(rotulo, df, antes=None):
    mostrar(rotulo, df, antes)
    etapas.append((rotulo, len(df), None if antes is None else antes))
    return df


def pct(s):
    return (s.value_counts(normalize=True) * 100).round(1)


# 1. assinaturas
a = pd.read_csv(BRUTOS / "assinaturas.csv", dtype=str)
etapa("assinaturas.csv", a)
print("user_id distintos:", a["user_id"].nunique())

# 2. status ativa
n = len(a)
ativas = etapa("status_atual = ativa (inclui testes)", a[a["status_atual"].str.strip().str.lower() == "ativa"], n)

# 3. datas
inicio = para_brasilia(ativas["inicio"])
print("ativas com inicio > corte:", int((inicio > CORTE).sum()), "| inicio NaT:", int(inicio.isna().sum()))
print("ativas com data_fim preenchida:", int(ativas["data_fim"].fillna("").str.strip().ne("").sum()))

# 4. usuarios
u = pd.read_csv(BRUTOS / "usuarios.csv", usecols=["user_id", "email"], dtype=str)
etapa("usuarios.csv", u)
u["teste"] = u["email"].str.strip().str.lower().str.endswith(DOMINIO_TESTE, na=False)

# 5. testes
print("contas de teste em usuarios:", int(u["teste"].sum()))
j = ativas.merge(u[["user_id", "teste"]], on="user_id", how="left")
etapa("junção ativas x usuarios (esquerda)", j, len(ativas))
print("ativas sem user_id em usuarios:", int(j["teste"].isna().sum()))
t = j[j["teste"] == True]
print("testes entre as ativas:", len(t), "| plano:", t["plano_atual"].value_counts().to_dict(),
      "| canal:", t["canal_cobranca"].value_counts().to_dict())

# 6. sem testes
n = len(j)
p = etapa("ativas sem contas de teste (pagantes no corte)", j[j["teste"] == False], n)

# saídas
por_plano = p["plano_atual"].value_counts()
por_canal = p["canal_cobranca"].value_counts()
assert por_plano.sum() == len(p) == por_canal.sum(), "soma por plano/canal não bate"
print("\nTOTAL:", len(p))
print(pd.DataFrame({"n": por_plano, "%": pct(p["plano_atual"])}))
print(pd.DataFrame({"n": por_canal, "%": pct(p["canal_cobranca"])}))

# tres contas para conferir à mão
amostra = []
for plano_canal in (["app_store", "google_play"], ["web_cartao", "web_pix"]):
    amostra.append(p[p["canal_cobranca"].isin(plano_canal)].sample(2, random_state=8))
amostra = pd.concat(amostra).head(3)[["assinatura_id", "user_id", "plano_atual", "canal_cobranca", "inicio"]]
print("\nContas para conferir:\n", amostra.to_string(index=False))

# relatório
def tab(df):
    return df.to_markdown() if hasattr(df, "to_markdown") else df.to_string()

linhas = ["# Pagantes ativos no corte (30/09/2026)", "",
          f"**Total: {len(p):,}**".replace(",", "."), "",
          "O retrato bruto de `assinaturas.csv` tem 14.813 ativas, mas inclui as 60 contas de teste.", "",
          "## Filtros", "", "| Etapa | Linhas |", "|---|---:|"]
linhas += [f"| {r} | {n:,} |".replace(",", ".") for r, n, _ in etapas]
linhas += ["", "## Por plano", "", "| Plano | n | % |", "|---|---:|---:|"]
linhas += [f"| {k} | {v:,} | {pct(p['plano_atual'])[k]} |".replace(",", ".") for k, v in por_plano.items()]
linhas += ["", "## Por canal de cobrança", "", "| Canal | n | % |", "|---|---:|---:|"]
linhas += [f"| {k} | {v:,} | {pct(p['canal_cobranca'])[k]} |".replace(",", ".") for k, v in por_canal.items()]
SAIDAS.joinpath("pagantes_ativos_corte.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
